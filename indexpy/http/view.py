import functools
import typing

from indexpy.concurrency import keepasync
from indexpy.openapi.functions import bound_params, parse_params
from indexpy.types import LOWER_HTTP_METHODS, UPPER_HTTP_METHODS
from indexpy.utils import cached

from .request import Request
from .responses import Response

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
