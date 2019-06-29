from starlette.responses import Response

from .config import logger


class View:
    http_method_names = ['get', 'post', 'put', 'patch', 'delete', 'head', 'options', 'trace']

    def __init__(self):
        pass

    def dispatch(self, request):
        # Try to dispatch to the right method; if a method doesn't exist,
        # defer to the error handler. Also defer to the error handler if the
        # request method isn't on the approved list.
        self.request = request

        if self.request.method.lower() in self.http_method_names:
            handler = getattr(self, self.request.method.lower(), self.http_method_not_allowed)
        else:
            handler = self.http_method_not_allowed
        return handler()

    def http_method_not_allowed(self):
        logger.warning(f'Method Not Allowed ({self.request.method}): {self.request.url.path}')
        return Response(status_code=405, headers={
            "Allow": ', '.join(self.allowed_methods())
        })

    def options(self):
        """Handle responding to requests for the OPTIONS HTTP verb."""
        return Response(headers={
            "Allow": ', '.join(self.allowed_methods()),
            "Content-Length": "0"
        })

    def allowed_methods(self):
        return [m.upper() for m in self.http_method_names if hasattr(self, m)]
