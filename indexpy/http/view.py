import typing
import functools
from inspect import signature

from pydantic import BaseModel, ValidationError

from ..concurrency import keepasync
from .responses import Response, automatic
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


class ViewMeta(keepasync(*HTTP_METHOD_NAMES)):  # type: ignore
    def __init__(
        cls,
        name: str,
        bases: typing.Tuple[type],
        namespace: typing.Dict[str, typing.Any],
    ):
        param_names = ["query", "header", "cookie", "body"]

        for key in filter(lambda key: key in HTTP_METHOD_NAMES, namespace.keys()):
            function = namespace[key]
            sig = signature(function)

            setattr(
                function,
                "__params__",
                {
                    param_name: sig.parameters[param_name].annotation
                    for param_name in param_names
                    if (
                        param_name in sig.parameters
                        and issubclass(sig.parameters[param_name].annotation, BaseModel)
                    )
                },
            )
        super().__init__(name, bases, namespace)


def merge_list(
    raw: typing.List[typing.Tuple[str, str]]
) -> typing.Dict[str, typing.Union[typing.List[str], str]]:
    """
    If there are values with the same key value, they are merged into a List.
    """
    d: typing.Dict[str, typing.Union[typing.List[str], str]] = {}
    for k, v in raw:
        if k in d:
            if isinstance(d[k], list):
                typing.cast(typing.List, d[k]).append(v)
            else:
                d[k] = [typing.cast(str, d[k]), v]
        else:
            d[k] = v
    return d


class HTTPView(metaclass=ViewMeta):  # type: ignore
    def __init__(self, request: Request) -> None:
        self.request = request

    def __await__(self):
        return self.__call__().__await__()

    @staticmethod
    async def partial(handler: typing.Callable, request: Request) -> typing.Any:
        __params__ = getattr(handler, "__params__", {})

        if not __params__:
            return handler

        params: typing.Dict[str, BaseModel] = {}

        # try to get parameters model and parse
        if "query" in __params__:
            params["query"] = __params__["query"](
                **merge_list(request.query_params.multi_items())
            )

        if "header" in __params__:
            params["header"] = __params__["header"](
                **merge_list(request.headers.items())
            )

        if "cookie" in __params__:
            params["cookie"] = __params__["cookie"](**request.cookies)

        # try to get body model and parse
        if "body" in __params__:
            if request.headers.get("Content-Type") == "application/json":
                _body_data = await request.json()
            else:
                _body_data = await request.form()
            params["body"] = __params__["body"](**_body_data)

        return functools.partial(handler, **params)

    async def __call__(self) -> Response:
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
            resp = await self.catch_validation_error(e)
        else:
            resp = await handler()

        if isinstance(resp, tuple):
            resp = automatic(*resp)
        else:
            resp = automatic(resp)
        return resp

    async def catch_validation_error(
        self, e: ValidationError
    ) -> typing.Union[Response, tuple]:
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
