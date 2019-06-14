from starlette.responses import Response

from .config import get_logger

logger = get_logger()


class View:
    http_method_names = ['get', 'post', 'put', 'patch', 'delete', 'head', 'options', 'trace']

    def __init__(self, request):
        self.request = request

    def dispatch(self):
        # Try to dispatch to the right method; if a method doesn't exist,
        # defer to the error handler. Also defer to the error handler if the
        # request method isn't on the approved list.
        if self.request.method.lower() in self.http_method_names:
            handler = getattr(self, self.request.method.lower(), self.http_method_not_allowed)
        else:
            handler = self.http_method_not_allowed
        return handler(self.request)

    def http_method_not_allowed(self, *args, **kwargs):
        logger.warning(
            'Method Not Allowed (%s): %s', self.request.method, self.request.url.path,
            extra={'status_code': 405, 'request': self.request}
        )
        return Response(status_code=405, headers={
            "Allow": ', '.join(self._allowed_methods())
        })

    def options(self, *args, **kwargs):
        """Handle responding to requests for the OPTIONS HTTP verb."""
        return Response(headers={
            "Allow": ', '.join(self._allowed_methods()),
            "Content-Length": "0"
        })

    def _allowed_methods(self):
        return [m.upper() for m in self.http_method_names if hasattr(self, m)]
