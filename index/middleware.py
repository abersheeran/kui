import typing

from starlette.requests import Request
from starlette.responses import Response

from .types import AsyncCallable
from .concurrency import keepasync


class MiddlewareMixin(metaclass=keepasync("process_request", "process_response")):

    ChildMiddlewares: typing.Iterable[typing.Callable] = ()

    def __init__(self, get_response: AsyncCallable) -> None:
        self.get_response = self.mount_middleware(get_response)

    def mount_middleware(self, get_response: AsyncCallable) -> AsyncCallable:
        for base_middleware in self.ChildMiddlewares:
            get_response = base_middleware(get_response)
        return get_response

    async def __call__(self, request: Request) -> Response:
        response = None
        if hasattr(self, "process_request"):
            response = await self.process_request(request)

        if response is None:
            response = await self.get_response(request)

        if hasattr(self, "process_response"):
            response = await self.process_response(request, response)
        return response
