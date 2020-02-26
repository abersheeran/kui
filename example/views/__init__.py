from indexpy.middleware import MiddlewareMixin
from indexpy import logger


class ExampleChildMiddleware(MiddlewareMixin):
    async def process_request(self, request):
        logger.debug("enter first process request")

    async def process_response(self, request, response):
        logger.debug("enter last process response")
        return response


class Middleware(MiddlewareMixin):
    mounts = (ExampleChildMiddleware,)

    async def process_request(self, request):
        logger.debug("example base middleware request")

    async def process_response(self, request, response):
        logger.debug("example base middleware response")
        return response
