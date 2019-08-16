import typing
from .concurrency import keepasync


class MiddlewareMixin(metaclass=keepasync('process_request', 'process_response')):

    def __init__(self, get_response: typing.Callable):
        self.get_response = get_response

    async def __call__(self, request):
        response = None
        if hasattr(self, 'process_request'):
            response = await self.process_request(request)

        if response is None:
            response = await self.get_response(request)

        if hasattr(self, 'process_response'):
            response = await self.process_response(request, response)
        return response
