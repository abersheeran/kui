from index.middleware import MiddlewareMixin
from index.config import logger


class Middleware(MiddlewareMixin):

    async def process_request(self, request):
        print("enter first process request")

    async def process_response(self, request, response):
        print("enter last process response")
        return response
