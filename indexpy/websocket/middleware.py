from __future__ import annotations

import typing

from indexpy.concurrency import keepasync

if typing.TYPE_CHECKING:
    from .request import WebSocket

MiddlewareMeta = keepasync("before_accept", "after_close", "catch_error")


class MiddlewareMixin(metaclass=MiddlewareMeta):  # type: ignore

    mounts: typing.Sequence[typing.Callable] = ()

    def __init__(self, websocket_handler: typing.Callable) -> None:
        self.websocket_handler = self.mount_middleware(websocket_handler)

    def mount_middleware(self, websocket_handler: typing.Callable) -> typing.Callable:
        for middleware in reversed(self.mounts):
            websocket_handler = middleware(websocket_handler)
        return websocket_handler

    async def __call__(self, websocket: WebSocket) -> None:
        await self.before_accept(websocket)
        try:
            await self.websocket_handler(websocket)
        except Exception as exc:
            await self.catch_error(websocket, exc)
        await self.after_close(websocket)

    async def before_accept(self, websocket: WebSocket) -> None:
        """
        Called before calling websocket handler
        """

    async def after_close(self, websocket: WebSocket) -> None:
        """
        Called after the websocket handler has finished processing
        """

    async def catch_error(self, websocket: WebSocket, exception: Exception) -> None:
        """
        Called after the websocket handler raise Exception
        """
