from indexpy.middleware import MiddlewareMixin
from indexpy import logger


class Middleware(MiddlewareMixin):
    async def process_request(self, request):
        logger.debug("enter second process request")

    async def process_response(self, request, response):
        logger.debug("enter second last process response")
        return response
