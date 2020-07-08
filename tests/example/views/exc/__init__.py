from indexpy.http import MiddlewareMixin


class Middleware(MiddlewareMixin):
    async def process_exception(self, request, exception):
        if isinstance(exception, NotImplementedError):
            return "NotImplementedError in /exc/*", 500
