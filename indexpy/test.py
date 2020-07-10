import os
import ast
import sys
import typing

import click
from uvicorn.importer import import_from_string
from starlette.testclient import TestClient as _TestClient, ASGI2App, ASGI3App
from requests import Response, Session

from .applications import Index
from .config import Config


class TestClient:
    def __init__(
        self,
        app: typing.Union[ASGI2App, ASGI3App],
        uri: str = "",
        base_url: str = "http://testserver",
        raise_server_exceptions: bool = True,
        root_path: str = "",
    ) -> None:
        self.uri = uri
        self.__client = _TestClient(app, base_url, raise_server_exceptions, root_path)

    def get(self, *args, **kwargs) -> Response:
        return self.__client.get(self.uri, *args, **kwargs)

    def options(self, *args, **kwargs) -> Response:
        return self.__client.options(self.uri, *args, **kwargs)

    def head(self, *args, **kwargs) -> Response:
        return self.__client.head(self.uri, *args, **kwargs)

    def post(self, *args, **kwargs) -> Response:
        return self.__client.post(self.uri, *args, **kwargs)

    def put(self, *args, **kwargs) -> Response:
        return self.__client.put(self.uri, *args, **kwargs)

    def patch(self, *args, **kwargs) -> Response:
        return self.__client.patch(self.uri, *args, **kwargs)

    def delete(self, *args, **kwargs) -> Response:
        return self.__client.delete(self.uri, *args, **kwargs)

    def websocket_connect(
        self, subprotocols: typing.Sequence[str] = None, **kwargs: typing.Any
    ) -> typing.Any:
        return self.__client.websocket_connect(
            self.uri, subprotocols=subprotocols, **kwargs
        )

    def __enter__(self) -> Session:
        return self.__client.__enter__()

    def __exit__(self, *args: typing.Any) -> None:
        return self.__client.__exit__()


__global_test_app__: typing.Optional[Index] = None


def get_test_app() -> Index:
    assert __global_test_app__
    return __global_test_app__


class TestView:
    @property
    def client(self) -> TestClient:
        app = __global_test_app__
        assert app is not None
        path = app.indexfile.get_path_from_module_name(self.__class__.__module__)
        if path is None:
            raise Exception("What's wrong with you?")
        return TestClient(app, path)


class LiteralOption(click.Option):
    def type_cast_value(self, ctx, value):
        try:
            return ast.literal_eval(value)
        except Exception:
            raise click.BadParameter(value)


def _convert_path(app: Index, path: str) -> str:
    if ".py" in path:
        return path
    elif "::" in path:
        pathlist = path.split("::")
        pathlist[0] = app.indexfile.get_filepath_from_path(pathlist[0])
        return "::".join(pathlist)
    else:
        return app.indexfile.get_filepath_from_path(path)


@click.option(
    "-app",
    "--application",
    default=lambda: Config().APP,
    help="ASGI Application, like: main:app",
)
@click.option("--args", cls=LiteralOption, default="[]")
@click.argument("path", default="")
def cmd_test(application: str, args: typing.List[str], path: str):
    import pytest

    global __global_test_app__
    app: Index = import_from_string(application)
    __global_test_app__ = app

    pytest_args = [
        f"--rootdir={os.getcwd()}",
        "--override-ini=python_files=views/*.py",
        "--override-ini=python_classes=Test",
        "--override-ini=python_functions=test_*",
    ]
    pytest_args.extend(args)

    if path:
        pytest_args.append(_convert_path(app, path))

    with _TestClient(app):
        sys.exit(pytest.main(pytest_args))
