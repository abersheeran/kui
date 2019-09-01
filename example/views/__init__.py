from index.middleware import MiddlewareMixin
from index.config import logger


class ExampleChildMiddleware(MiddlewareMixin):

    async def process_request(self, request):
        logger.info("example base middleware request")

    async def process_response(self, request, response):
        logger.info("example base middleware response")
        return response


class Middleware(MiddlewareMixin):

    ChildMiddlwares = (ExampleChildMiddleware, )

    async def process_request(self, request):
        logger.info("enter first process request")

    async def process_response(self, request, response):
        logger.info("enter last process response")
        return response
