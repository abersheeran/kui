import typing

from indexpy.routing.routes import BaseRoute, HttpRoute, Routes


_RoutesSelf = typing.TypeVar("_RoutesSelf", bound="MultimethodRoutes")


class MultimethodRoutes(Routes):
    def append(self: _RoutesSelf, route: BaseRoute) -> _RoutesSelf:
        if isinstance(route, HttpRoute) and hasattr(route.endpoint, "__method__"):
            for r in self:
                if r.path == route.path and isinstance(route, HttpRoute):
                    if not hasattr(r, "__method__"):
                        raise RuntimeError("")  # TODO
                    else:
                        pass
        return super().append(route)
