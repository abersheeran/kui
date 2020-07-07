from indexpy.http import MiddlewareMixin


class EmptyMiddleware(MiddlewareMixin):
    pass


class Middleware(MiddlewareMixin):
    mounts = (EmptyMiddleware,)

    async def process_request(self, request):
        print("enter second process request")

    async def process_response(self, request, response):
        print("enter second last process response")
        return response
