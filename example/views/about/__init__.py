from index.middleware import MiddlewareMixin
from index.config import logger


class Middleware(MiddlewareMixin):
    async def process_request(self, request):
        logger.info("enter second process request")

    async def process_response(self, request, response):
        logger.info("enter second last process response")
        return response
