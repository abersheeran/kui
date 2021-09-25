import typing
from functools import wraps

from ...routing import BaseRoute, HttpRoute, Routes
from ...views import HttpView

_RoutesSelf = typing.TypeVar("_RoutesSelf", bound="MultimethodRoutes")

exclude_self = lambda func: wraps(func)(
    lambda self, *args, **kwargs: func(*args, **kwargs)
)


class MultimethodRoutes(Routes):
    def __init__(
        self,
        *iterable: typing.Union[BaseRoute, typing.Iterable[BaseRoute]],
        namespace: str = "",
        tags: typing.Iterable[str] = None,
        http_middlewares: typing.Sequence[typing.Any] = [],
        socket_middlewares: typing.Sequence[typing.Any] = [],
        base_class: typing.Type[HttpView] = HttpView,
    ) -> None:
        super().__init__(
            *iterable,
            namespace=namespace,
            tags=tags,
            http_middlewares=http_middlewares,
            socket_middlewares=socket_middlewares,
        )
        self.base_class = base_class

    def append(self: _RoutesSelf, route: BaseRoute) -> _RoutesSelf:
        if hasattr(route.endpoint, "__methods__"):
            raise TypeError("MultimethodRoutes not allow use class-base view.")

        if not isinstance(route, HttpRoute):
            self._list.append(route)
            return self

        try:
            r = next(
                filter(
                    lambda r: isinstance(r, HttpRoute) and r.path == route.path,
                    self._list,
                )
            )
            if not hasattr(route.endpoint, "__method__") or not (
                hasattr(r.endpoint, "__method__") or hasattr(r.endpoint, "__methods__")
            ):
                raise RuntimeError(
                    f"Routing '{route.path}' conflict, can be resolved by restricting the request method."
                )
        except StopIteration:
            self._list.append(route)
        else:
            if hasattr(r.endpoint, "__methods__"):
                endpoint = type(
                    r.endpoint.__name__,
                    (self.base_class, _MultiMethodView),
                    {
                        **{
                            method.lower(): getattr(r.endpoint, method.lower())
                            for method in r.endpoint.__methods__  # type: ignore
                        },
                        route.endpoint.__method__.lower(): exclude_self(route.endpoint),  # type: ignore
                    },
                )
            else:
                endpoint = type(
                    "_MultimethodEndpoint",
                    (self.base_class, _MultiMethodView),
                    {
                        r.endpoint.__method__.lower(): exclude_self(r.endpoint),  # type: ignore
                        route.endpoint.__method__.lower(): exclude_self(route.endpoint),  # type: ignore
                    },
                )
            # replacing route inplace
            r.endpoint = endpoint
        return self


class _MultiMethodView:
    """
    Just as a mark
    """


def is_multimethod_view(cls: type) -> bool:
    return isinstance(cls, type) and issubclass(cls, _MultiMethodView)
