from .concurrency import complicating


class MiddlewareMixin:
    def __init__(self, get_response):
        self.get_response = get_response

    async def __call__(self, request):
        response = None
        if hasattr(self, 'process_request'):
            response = await complicating(self.process_request)(request)

        if response is None:
            response = await self.get_response(request)

        if hasattr(self, 'process_response'):
            response = await complicating(self.process_response)(request, response)
        return response
