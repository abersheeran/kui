import typing

from ..concurrency import keepasync
from .responses import Response, automatic
from .request import Request


MiddlewareMeta = keepasync("process_request", "process_response")


class MiddlewareMixin(metaclass=MiddlewareMeta):  # type: ignore

    mounts: typing.Sequence[typing.Callable] = ()

    def __init__(self, get_response: typing.Callable) -> None:
        self.get_response = self.mount_middleware(get_response)

    def mount_middleware(self, get_response: typing.Callable) -> typing.Callable:
        for middleware in reversed(self.mounts):
            get_response = middleware(get_response)
        return get_response

    async def __call__(self, request: Request) -> Response:
        response = await self.process_request(request)

        if response is None:
            response = await self.get_response(request)

        if isinstance(response, tuple):
            response = automatic(*response)
        else:
            response = automatic(response)

        response = await self.process_response(request, response)

        return response

    async def process_request(self, request: Request) -> typing.Union[None, typing.Any]:
        """Must return None, otherwise return the value as the result of this request."""

    async def process_response(self, request: Request, response: Response) -> Response:
        return response
