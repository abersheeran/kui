from __future__ import annotations

from dataclasses import dataclass
from typing import ClassVar

from ..routing import AsyncViewType
from ..routing import HttpRoute as _HttpRoute
from ..routing import Router as _Router
from ..routing import Routes as _Routes
from ..routing import SocketRoute as _SocketRoute
from ..routing.extensions import MultimethodRoutes as _MultimethodRoutes
from .parameters import auto_params


@dataclass
class HttpRoute(_HttpRoute[AsyncViewType]):
    _auto_params: ClassVar = lambda cls, *args, **kwargs: auto_params(*args, **kwargs)


@dataclass
class SocketRoute(_SocketRoute[AsyncViewType]):
    _auto_params: ClassVar = lambda cls, *args, **kwargs: auto_params(*args, **kwargs)


class Routes(_Routes[AsyncViewType]):
    pass


class MultimethodRoutes(_MultimethodRoutes[AsyncViewType]):
    pass


class Router(_Router[AsyncViewType]):
    pass


__all__ = [
    "HttpRoute",
    "SocketRoute",
    "Routes",
    "MultimethodRoutes",
]
