import importlib
import typing
from functools import reduce, update_wrapper
from pathlib import Path

from ...routing.routes import BaseRoute, HttpRoute, SocketRoute
from ...utils import F


class FileRoutes(typing.Iterable[BaseRoute]):
    def __init__(
        self,
        module_name: str,
        *,
        namespace: str = "",
        allow_underline: bool = False,
        suffix: str = "",
    ) -> None:
        dirpath = Path(importlib.import_module(module_name).__file__).absolute().parent

        self.namespace = namespace
        self._list: typing.List[typing.Union[HttpRoute, SocketRoute]] = []

        for relpath in map(
            lambda pypath: (
                dirpath
                | F(pypath.relative_to)
                | F(str)
                | F(lambda path: path.replace("\\", "/"))
                | F(lambda path: path[:-3])
            ),
            dirpath.glob("**/*.py"),
        ):
            url_path = (
                ("/" + relpath)
                | F(lambda path: (allow_underline or path) and path.replace("_", "-"))
                | F(
                    lambda path: path[:-5] if path.endswith("/index") else path + suffix
                )
            )
            path_list = [module_name, *relpath.split("/")]
            module = importlib.import_module(".".join(path_list))

            append_route = lambda view, middleware_name, route_type: (
                range(len(path_list), 0, -1)
                | F(map, lambda deep: ".".join(path_list[:deep]))
                | F(map, lambda module_name: importlib.import_module(module_name))
                | F(map, lambda module: getattr(module, middleware_name, None))
                | F(filter, lambda middleware: middleware is not None)
                | F(reduce, lambda h, m: update_wrapper(m(h), h), ..., view)
                | F(route_type, url_path, ..., getattr(module, "name", None))
                | F(self._list.append)
            )
            getattr(module, "HTTP", None) | F(
                lambda view: (
                    view is None or append_route(view, "HTTPMiddleware", HttpRoute)
                )
            )
            getattr(module, "Socket", None) | F(
                lambda view: (
                    view is None or append_route(view, "SocketMiddleware", SocketRoute)
                )
            )

    def __iter__(self) -> typing.Iterator[BaseRoute]:
        return iter(self._list)
