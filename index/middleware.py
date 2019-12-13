import typing

from starlette.requests import Request
from starlette.responses import Response

from .concurrency import keepasync
from .responses import automatic


class MiddlewareMixin(metaclass=keepasync("process_request", "process_response")):

    ChildMiddlewares: typing.Iterable[typing.Callable] = ()

    def __init__(self, get_response: typing.Callable) -> None:
        self.get_response = self.mount_middleware(get_response)

    def mount_middleware(self, get_response: typing.Callable) -> typing.Callable:
        for base_middleware in self.ChildMiddlewares:
            get_response = base_middleware(get_response)
        return get_response

    async def __call__(self, request: Request) -> Response:
        response = None
        if hasattr(self, "process_request"):
            response = await self.process_request(request)

        if response is None:
            response = await self.get_response(request)

        if not isinstance(response, tuple):
            response = (response,)
        response = automatic(*response)

        if hasattr(self, "process_response"):
            response = await self.process_response(request, response)
        return response
