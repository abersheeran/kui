import asyncio
import typing
import logging

from starlette.responses import Response
from starlette.requests import Request
from starlette.concurrency import run_in_threadpool

from .responses import automatic
from .concurrency import keepasync

logger = logging.getLogger(__name__)

HTTP_METHOD_NAMES = ['get', 'post', 'put', 'patch', 'delete', 'head', 'options', 'trace']


class View(metaclass=keepasync(*HTTP_METHOD_NAMES)):

    def __init__(self):
        pass

    async def __call__(self, request: Request) -> Response:
        # Try to dispatch to the right method; if a method doesn't exist,
        # defer to the error handler. Also defer to the error handler if the
        # request method isn't on the approved list.
        self.request = request

        if self.request.method.lower() in HTTP_METHOD_NAMES:
            handler = getattr(self, self.request.method.lower(), self.http_method_not_allowed)
        else:
            handler = self.http_method_not_allowed

        resp = await handler()

        if not isinstance(resp, tuple):
            resp = (resp,)
        return automatic(*resp)

    async def http_method_not_allowed(self):
        logger.warning(f'Method Not Allowed ({self.request.method}): {self.request.url.path}')
        return Response(status_code=405, headers={
            "Allow": ', '.join(self.allowed_methods())
        })

    async def options(self):
        """Handle responding to requests for the OPTIONS HTTP verb."""
        return Response(headers={
            "Allow": ', '.join(self.allowed_methods()),
            "Content-Length": "0"
        })

    def allowed_methods(self):
        return [m.upper() for m in HTTP_METHOD_NAMES if hasattr(self, m)]
