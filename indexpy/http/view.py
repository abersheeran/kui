import functools
import typing
from inspect import signature

from pydantic import BaseModel, ValidationError

from indexpy.concurrency import keepasync
from indexpy.types import LOWER_HTTP_METHODS, UPPER_HTTP_METHODS
from indexpy.utils import cached

from .exceptions import ParamsValidationError
from .request import Request
from .responses import Response

T = typing.TypeVar("T", bound=typing.Callable)

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


def parse_params(function: T) -> T:
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
            and not issubclass(sig.parameters[param_name].annotation, BaseModel)
        )
    ]
    if incorrect_keys:
        raise TypeError(
            f"Params {incorrect_keys} annotation is incorrect in `{function.__name__}`. "
            + "You should inherit `pydantic.BaseModel`."
        )

    params = {
        param_name: sig.parameters[param_name].annotation
        for param_name in param_names
        if (
            param_name in sig.parameters
            and issubclass(sig.parameters[param_name].annotation, BaseModel)
        )
    }
    if "body" in params:
        setattr(function, "__request_body__", params.pop("body"))
    if params:
        setattr(function, "__parameters__", params)
    return function


def _merge_multi_value(raw_list):
    """
    If there are values with the same key value, they are merged into a List.
    """
    d = {}
    for k, v in raw_list:
        if k not in d:
            d[k] = v
            continue
        if isinstance(d[k], list):
            d[k].append(v)
        else:
            d[k] = [d[k], v]
    return d


async def bound_params(handler: typing.Callable, request: Request) -> typing.Callable:
    """
    bound parameters "path", "query", "header", "cookie", "body" to the view function
    """
    parameters = getattr(handler, "__parameters__", None)
    request_body = getattr(handler, "__request_body__", None)
    if not (parameters or request_body):
        return handler

    kwargs: typing.Dict[str, BaseModel] = {}

    try:
        # try to get parameters model and parse
        if parameters:
            if "path" in parameters:
                kwargs["path"] = parameters["path"](**request.path_params)

            if "query" in parameters:
                kwargs["query"] = parameters["query"](
                    **_merge_multi_value(request.query_params.multi_items())
                )

            if "header" in parameters:
                kwargs["header"] = parameters["header"](
                    **_merge_multi_value(request.headers.items())
                )

            if "cookie" in parameters:
                kwargs["cookie"] = parameters["cookie"](**request.cookies)

        # try to get body model and parse
        if request_body:
            if request.headers.get("Content-Type") == "application/json":
                _body_data = await request.json()
            else:
                _body_data = await request.form()
            kwargs["body"] = request_body(**_body_data)

    except ValidationError as e:
        raise ParamsValidationError(e)

    return functools.partial(handler, **kwargs)


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
            namespace[function_name] = parse_params(function)

        setattr(
            cls,
            "__methods__",
            [m.upper() for m in HTTP_METHOD_NAMES if hasattr(cls, m)],
        )

        super().__init__(name, bases, namespace)


class HTTPView(metaclass=ViewMeta):  # type: ignore
    if typing.TYPE_CHECKING:
        __methods__: typing.List[UPPER_HTTP_METHODS]

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

        handler = await bound_params(handler, self.request)

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


@cached
def only_allow(
    method: LOWER_HTTP_METHODS, func: typing.Callable = None
) -> typing.Callable:
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

    func = parse_params(func)

    @functools.wraps(func)
    async def wrapper(*args, **kwargs) -> typing.Any:
        request = args[0]
        if request.method.lower() == method.lower():
            handler = await bound_params(func, request)  # type: ignore
            return await handler(*args, **kwargs)

        if request.method == "OPTIONS":
            return Response(headers={"Allow": method, "Content-Length": "0"})
        elif request.method in ("GET", "HEAD"):
            status_code = 404
        else:
            status_code = 405
        return Response(status_code=status_code)

    setattr(wrapper, "__method__", method.upper())
    return wrapper
