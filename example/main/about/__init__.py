from index.middleware import MiddlewareMixin
from index.config import logger


class Middleware(MiddlewareMixin):

    def process_request(self, request):
        print("enter second process request")

    def process_response(self, request, response):
        print("enter second last process response")
        return response
