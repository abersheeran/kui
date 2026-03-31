from __future__ import annotations

from dataclasses import dataclass
from typing import ClassVar

from ..routing import HttpRoute as _HttpRoute
from ..routing import Router as _Router
from ..routing import Routes as _Routes
from ..routing import SocketRoute as _SocketRoute
from ..routing import SyncViewType
from ..routing.extensions import MultimethodRoutes as _MultimethodRoutes
from .parameters import auto_params
from .views import required_method


@dataclass
class HttpRoute(_HttpRoute[SyncViewType]):
    _auto_params: ClassVar = lambda cls, *args, **kwargs: auto_params(*args, **kwargs)


@dataclass
class SocketRoute(_SocketRoute[SyncViewType]):
    _auto_params: ClassVar = lambda cls, *args, **kwargs: auto_params(*args, **kwargs)


class Routes(_Routes[SyncViewType]):
    _http_route_class = HttpRoute
    _required_method_factory = staticmethod(required_method)


class MultimethodRoutes(_MultimethodRoutes[SyncViewType]):
    _http_route_class = HttpRoute
    _required_method_factory = staticmethod(required_method)


class Router(_Router[SyncViewType]):
    _http_route_class = HttpRoute
    _required_method_factory = staticmethod(required_method)


__all__ = [
    "HttpRoute",
    "SocketRoute",
    "Routes",
    "MultimethodRoutes",
]
