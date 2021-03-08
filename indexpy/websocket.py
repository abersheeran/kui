from __future__ import annotations

from contextvars import ContextVar

from baize.asgi import WebSocket as BaiZeWebSocket

from .http.request import HTTPConnection


class WebSocket(BaiZeWebSocket, HTTPConnection):
    pass


websocket: ContextVar[WebSocket] = ContextVar("websocket")
