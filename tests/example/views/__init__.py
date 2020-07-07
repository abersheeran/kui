from indexpy.http import MiddlewareMixin


class ExampleChildMiddleware(MiddlewareMixin):
    async def process_request(self, request):
        print("enter first process request")

    async def process_response(self, request, response):
        print("enter last process response")
        return response


class Middleware(MiddlewareMixin):
    mounts = (ExampleChildMiddleware,)

    async def process_request(self, request):
        print("example base middleware request")

    async def process_response(self, request, response):
        print("example base middleware response")
        return response
