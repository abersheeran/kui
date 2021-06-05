import typing

from indexpy.routing.routes import BaseRoute, HttpRoute, Routes
from indexpy.views import HttpView

_RoutesSelf = typing.TypeVar("_RoutesSelf", bound="MultimethodRoutes")


class MultimethodRoutes(Routes):
    def __init__(
        self,
        *iterable: typing.Union[BaseRoute, typing.Iterable[BaseRoute]],
        namespace: str,
        http_middlewares: typing.Sequence[typing.Any],
        socket_middlewares: typing.Sequence[typing.Any],
        base_class: typing.Type[HttpView] = HttpView
    ) -> None:
        super().__init__(
            *iterable,
            namespace=namespace,
            http_middlewares=http_middlewares,
            socket_middlewares=socket_middlewares,
        )
        self.base_class = base_class

    def append(self: _RoutesSelf, route: BaseRoute) -> _RoutesSelf:
        if hasattr(route.endpoint, "__methods__"):
            raise TypeError("MultimethodRoutes not allow use class-base view.")
        return super().append(route)

    def __iter__(self) -> typing.Iterator[BaseRoute]:
        result: typing.List[BaseRoute] = []
        for route in self._list:
            if isinstance(route, HttpRoute):
                pass  # TODO

        return iter(result)
