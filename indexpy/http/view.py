import typing
import functools
from inspect import signature

from pydantic import BaseModel, ValidationError

from ..concurrency import keepasync
from .responses import Response
from .request import Request


HTTP_METHOD_NAMES = [
    "get",
    "post",
    "put",
    "patch",
    "delete",
    "head",
    "options",
    "trace",
]


ViewMeta = keepasync(*HTTP_METHOD_NAMES)


class HTTPView(metaclass=ViewMeta):  # type: ignore
    def __init__(self, request: Request) -> None:
        self.request = request

    def __await__(self):
        return self.__call__().__await__()

    @staticmethod
    async def partial(
        handler: typing.Callable, request: Request
    ) -> typing.Optional[typing.Any]:

        sig = signature(handler)

        # try to get parameters model and parse
        query = sig.parameters.get("query")
        if query:
            assert issubclass(query.annotation, BaseModel)
            _query = query.annotation(**request.query_params.to_dict())
            handler = functools.partial(handler, query=_query)

        header = sig.parameters.get("header")
        if header:
            assert issubclass(header.annotation, BaseModel)
            _header = header.annotation(**request.headers.to_dict())
            handler = functools.partial(handler, header=_header)

        cookie = sig.parameters.get("cookie")
        if cookie:
            assert issubclass(cookie.annotation, BaseModel)
            _cookie = cookie.annotation(**request.cookies)
            handler = functools.partial(handler, cookie=_cookie)

        # try to get body model and parse
        body = sig.parameters.get("body")
        if body:
            assert issubclass(body.annotation, BaseModel)
            if request.headers.get("Content-Type") == "application/json":
                _body_data = await request.json()
            else:
                _body_data = await request.form()
            _body = body.annotation(**_body_data)
            handler = functools.partial(handler, body=_body)
        return handler

    async def __call__(self) -> typing.Union[Response, typing.Tuple]:
        # Try to dispatch to the right method; if a method doesn't exist,
        # defer to the error handler. Also defer to the error handler if the
        # request method isn't on the approved list.

        if self.request.method.lower() in HTTP_METHOD_NAMES:
            handler = getattr(
                self, self.request.method.lower(), self.http_method_not_allowed
            )
        else:
            handler = self.http_method_not_allowed

        try:
            handler = await self.partial(handler, self.request)
        except ValidationError as e:
            return await self.catch_validation_error(e)

        return await handler()

    async def catch_validation_error(
        self, e: ValidationError
    ) -> typing.Union[Response, typing.Tuple]:
        """
        Used to handle request parsing errors
        """
        return e.errors(), 400

    async def http_method_not_allowed(self) -> Response:
        return Response(
            status_code=405,
            headers={"Allow": ", ".join(self.allowed_methods()), "Content-Length": "0"},
        )

    async def options(self) -> Response:
        """Handle responding to requests for the OPTIONS HTTP verb."""
        return Response(
            headers={"Allow": ", ".join(self.allowed_methods()), "Content-Length": "0"}
        )

    @classmethod
    def allowed_methods(cls) -> typing.List[str]:
        return [m.upper() for m in HTTP_METHOD_NAMES if hasattr(cls, m)]
