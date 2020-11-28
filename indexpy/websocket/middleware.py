import typing

from indexpy.concurrency import keepasync

from .request import WebSocket

MiddlewareMeta = keepasync("before_accept", "after_close")


class MiddlewareMixin(metaclass=MiddlewareMeta):  # type: ignore

    mounts: typing.Sequence[typing.Callable] = ()

    def __init__(self, get_response: typing.Callable) -> None:
        self.get_response = self.mount_middleware(get_response)

    def mount_middleware(self, get_response: typing.Callable) -> typing.Callable:
        for middleware in reversed(self.mounts):
            get_response = middleware(get_response)
        return get_response

    async def __call__(self, websocket: WebSocket) -> None:
        await self.before_accept(websocket)
        await self.get_response(websocket)
        await self.after_close(websocket)

    async def before_accept(self, websocket: WebSocket) -> None:
        """
        Called before calling websocket handler
        """

    async def after_close(self, websocket: WebSocket) -> None:
        """
        Called after the websocket handler has finished processing
        """
