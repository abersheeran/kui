import typing

from indexpy.routing.routes import BaseRoute, HttpRoute, Routes
from indexpy.views import HttpView

_RoutesSelf = typing.TypeVar("_RoutesSelf", bound="MultimethodRoutes")


class MultimethodRoutes(Routes):
    def __init__(
        self,
        *iterable: typing.Union[BaseRoute, typing.Iterable[BaseRoute]],
        namespace: str = "",
        http_middlewares: typing.Sequence[typing.Any] = [],
        socket_middlewares: typing.Sequence[typing.Any] = [],
        base_class: typing.Type[HttpView] = HttpView,
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
            if not isinstance(route, HttpRoute):
                result.append(route)
                continue

            try:
                r = next(
                    filter(
                        lambda r: isinstance(r, HttpRoute) and r.path == route.path,
                        result,
                    )
                )
                if not hasattr(route.endpoint, "__method__") or not (
                    hasattr(r.endpoint, "__method__")
                    or hasattr(r.endpoint, "__methods__")
                ):
                    raise RuntimeError(
                        f"Routing '{route.path}' conflict, can be resolved by restricting the request method."
                    )
            except StopIteration:
                result.append(route)
            else:
                if hasattr(r.endpoint, "__methods__"):
                    endpoint = type(
                        r.endpoint.__name__,
                        (self.base_class,),
                        {
                            **{
                                method.lower(): getattr(r.endpoint, method.lower())
                                for method in r.endpoint.__methods__
                            },
                            route.endpoint.__method__.lower(): route.endpoint,
                        },
                    )
                else:
                    endpoint = type(
                        "_Endpoint",
                        (self.base_class,),
                        {
                            r.endpoint.__method__.lower(): r.endpoint,
                            route.endpoint.__method__.lower(): route.endpoint,
                        },
                    )
                # replacing route inplace
                result[result.index(r)] = HttpRoute(
                    route.path, endpoint=endpoint, name=route.name
                )

        return iter(result)
