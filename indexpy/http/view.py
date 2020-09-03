import typing
import functools
import logging
from inspect import signature, isclass
from types import FunctionType

from pydantic import BaseModel, ValidationError

from ..types import ASGIApp
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


logger = logging.getLogger(__name__)


class ParamsValidationError(Exception):
    def __init__(self, validation_error: ValidationError) -> None:
        self.ve = validation_error


def bound_params(function: FunctionType) -> FunctionType:
    """
    parse function params "path", "query", "header", "cookie", "body"
    """
    param_names = ("path", "query", "header", "cookie", "body")
    sig = signature(function)

    incorrect_keys = [
        param_name
        for param_name in param_names
        if (
            param_name in sig.parameters
            and param_name != "path"
            and not issubclass(sig.parameters[param_name].annotation, BaseModel)
        )
    ]
    if incorrect_keys:
        raise TypeError(
            f"Params {incorrect_keys} annotation is incorrect in `{function.__name__}`. "
            + "You should inherit `pydantic.BaseModel`."
        )

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
    return function


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


async def parse_params(
    handler: typing.Callable, request: Request
) -> typing.Callable[[Request], typing.Awaitable[ASGIApp]]:

    if isclass(handler):
        return handler

    __params__ = getattr(handler, "__params__", {})
    if not __params__:
        return handler

    params: typing.Dict[str, BaseModel] = {}

    try:
        # try to get parameters model and parse
        if "path" in __params__:
            params["path"] = __params__["path"](**request.path_params)

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

    except ValidationError as e:
        raise ParamsValidationError(e)

    return functools.partial(handler, **params)


class ViewMeta(keepasync(*HTTP_METHOD_NAMES)):  # type: ignore
    def __init__(
        cls,
        name: str,
        bases: typing.Tuple[type],
        namespace: typing.Dict[str, typing.Any],
    ):

        for function_name in filter(
            lambda key: key in HTTP_METHOD_NAMES, namespace.keys()
        ):
            function = namespace[function_name]
            namespace[function_name] = bound_params(function)

        setattr(
            cls,
            "__methods__",
            [m.upper() for m in HTTP_METHOD_NAMES if hasattr(cls, m)],
        )

        super().__init__(name, bases, namespace)


class HTTPView(metaclass=ViewMeta):  # type: ignore
    if typing.TYPE_CHECKING:
        __methods__: typing.List[str]

    def __init__(self, request: Request) -> None:
        self.request = request

    def __await__(self) -> typing.Generator[typing.Any, None, Response]:
        return self.__impl__().__await__()

    async def __impl__(self) -> typing.Any:
        # Try to dispatch to the right method; if a method doesn't exist,
        # defer to the error handler.
        handler = getattr(
            self, self.request.method.lower(), self.http_method_not_allowed
        )

        handler = await parse_params(handler, self.request)

        return await handler()

    async def http_method_not_allowed(self) -> Response:
        if self.request.method not in ("GET", "HEAD"):
            status_code = 405
        else:
            status_code = 404

        return Response(
            status_code=status_code,
            headers={"Allow": ", ".join(self.__methods__), "Content-Length": "0"},
        )

    async def options(self) -> Response:
        """Handle responding to requests for the OPTIONS HTTP verb."""
        return Response(
            headers={"Allow": ", ".join(self.__methods__), "Content-Length": "0"}
        )


def only_allow(method: str = "", func: typing.Callable = None) -> typing.Callable:
    """
    Only allow the function to accept one type of request

    example:
        @only_allow("get")
        async def handle(request):
            ...
    or
        handle = only_allow("get", handle)
    """

    if method not in HTTP_METHOD_NAMES:
        raise ValueError(f"method must be in {HTTP_METHOD_NAMES}")

    if func is None:
        return lambda func: only_allow(method, func)

    setattr(func, "__method__", method.upper())

    @functools.wraps(func)
    async def wrapper(*args, **kwargs) -> typing.Any:
        request = args[0]
        if request.method.lower() == method.lower():
            return await func(*args, **kwargs)  # type: ignore

        if request.method == "OPTIONS":
            return Response(headers={"Allow": method, "Content-Length": "0"})
        elif request.method in ("GET", "HEAD"):
            status_code = 404
        else:
            status_code = 405
        return Response(status_code=status_code)

    return wrapper
