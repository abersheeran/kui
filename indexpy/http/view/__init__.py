import functools
import typing
from inspect import signature

from pydantic import BaseModel, ValidationError, create_model

from indexpy.concurrency import keepasync
from indexpy.types import LOWER_HTTP_METHODS, UPPER_HTTP_METHODS
from indexpy.utils import cached
from indexpy.http.exceptions import ParamsValidationError
from indexpy.http.request import Request
from indexpy.http.responses import Response

from .fields import PathInfo, QueryInfo, HeaderInfo, CookieInfo, BodyInfo, ExclusiveInfo

T = typing.TypeVar("T", bound=typing.Callable)


def parse_params(function: T) -> T:

    sig = signature(function)

    __parameters__ = {}
    __exclusive_models__ = {}
    path: typing.Dict[str, typing.Any] = {}
    query: typing.Dict[str, typing.Any] = {}
    header: typing.Dict[str, typing.Any] = {}
    cookie: typing.Dict[str, typing.Any] = {}
    body: typing.Dict[str, typing.Any] = {}

    for name, param in sig.parameters.items():
        default = param.default
        annotation = param.annotation

        if isinstance(default, QueryInfo):
            _type_ = query
        elif isinstance(default, HeaderInfo):
            _type_ = header
        elif isinstance(default, CookieInfo):
            _type_ = cookie
        elif isinstance(default, BodyInfo):
            _type_ = body
        elif isinstance(default, PathInfo):
            _type_ = path
        elif isinstance(default, ExclusiveInfo):
            if not issubclass(annotation, BaseModel):
                raise TypeError(
                    "The exclusive type must be a subclass of `pydantic.BaseModel`"
                )
            __parameters__[default.name] = annotation
            __exclusive_models__[annotation] = name
            continue
        else:
            continue

        if annotation != param.empty:
            _type_[name] = (annotation, default)
        else:
            _type_[name] = default

    __locals__ = locals()
    for key in filter(
        lambda key: bool(__locals__[key]), ("path", "query", "header", "cookie", "body")
    ):
        if key in __parameters__:
            raise RuntimeError(
                f'Exclusive("{key}") and {key.capitalize()} cannot be used at the same time'
            )
        __parameters__[key] = create_model("temporary_model", **locals()[key])  # type: ignore

    if "body" in __parameters__:
        setattr(function, "__request_body__", __parameters__.pop("body"))

    if __parameters__:
        setattr(function, "__parameters__", __parameters__)

    if __exclusive_models__:
        setattr(function, "__exclusive_models__", __exclusive_models__)

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
    exclusive_models = getattr(handler, "__exclusive_models__", {})
    if not (parameters or request_body):
        return handler

    kwargs: typing.Dict[str, BaseModel] = {}

    try:
        # try to get parameters model and parse
        if parameters:
            if "path" in parameters:
                _data_model = parameters["path"]
                _data = _data_model.parse_obj(request.path_params)
                if _data.__class__.__name__ == "temporary_model":
                    kwargs.update(_data.dict())
                else:
                    kwargs[exclusive_models[_data_model]] = _data

            if "query" in parameters:
                _data_model = parameters["query"]
                _data = _data_model.parse_obj(
                    _merge_multi_value(request.query_params.multi_items())
                )
                if _data.__class__.__name__ == "temporary_model":
                    kwargs.update(_data.dict())
                else:
                    kwargs[exclusive_models[_data_model]] = _data

            if "header" in parameters:
                _data_model = parameters["header"]
                _data = _data_model.parse_obj(
                    _merge_multi_value(request.headers.items())
                )
                if _data.__class__.__name__ == "temporary_model":
                    kwargs.update(_data.dict())
                else:
                    kwargs[exclusive_models[_data_model]] = _data

            if "cookie" in parameters:
                _data_model = parameters["cookie"]
                _data = _data_model.parse_obj(request.cookies)
                if _data.__class__.__name__ == "temporary_model":
                    kwargs.update(_data.dict())
                else:
                    kwargs[exclusive_models[_data_model]] = _data

        # try to get body model and parse
        if request_body:
            if request.headers.get("Content-Type") == "application/json":
                _body_data = await request.json()
            else:
                _body_data = _merge_multi_value((await request.form()).multi_items())
            _data = request_body.parse_obj(_body_data)
            if _data.__class__.__name__ == "temporary_model":
                kwargs.update(_data.dict())
            else:
                kwargs[exclusive_models[request_body]] = _data

    except ValidationError as e:
        raise ParamsValidationError(e)

    return functools.partial(handler, **kwargs)


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
        return Response(
            status_code=405,
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

        return Response(status_code=405)

    setattr(wrapper, "__method__", method.upper())
    return wrapper
