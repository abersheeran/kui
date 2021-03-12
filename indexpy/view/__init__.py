from __future__ import annotations

import asyncio
import functools
import typing
from itertools import groupby
from inspect import isclass, signature

from baize.asgi import FormData
from pydantic import BaseModel, ValidationError, create_model

from indexpy.exceptions import RequestValidationError
from indexpy.responses import Response, convert_response

if typing.TYPE_CHECKING:
    from indexpy.requests import Request

from .fields import BodyInfo, CookieInfo, ExclusiveInfo, HeaderInfo, PathInfo, QueryInfo


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


class ViewMeta(type):
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
            if asyncio.iscoroutinefunction(function):
                raise TypeError(
                    f"The function {function_name} should be defined using `async def`"
                )
            namespace[function_name] = parse_params(function)

        setattr(
            cls,
            "__methods__",
            [m.upper() for m in HTTP_METHOD_NAMES if hasattr(cls, m)],
        )

        super().__init__(name, bases, namespace)


class HTTPView(metaclass=ViewMeta):
    if typing.TYPE_CHECKING:
        __methods__: typing.List[str]

    def __init__(self, request: Request) -> None:
        self.request = request

    def __await__(self) -> typing.Generator[typing.Any, None, Response]:
        return self.__impl__().__await__()

    async def __impl__(self) -> Response:
        # Try to dispatch to the right method; if a method doesn't exist,
        # defer to the error handler.
        handler = getattr(
            self, self.request.method.lower(), self.http_method_not_allowed
        )

        handler = await bound_params(handler, self.request)

        return convert_response(await handler())

    async def http_method_not_allowed(self) -> Response:
        return Response(status_code=405, headers={"Allow": ", ".join(self.__methods__)})

    async def options(self) -> Response:
        """Handle responding to requests for the OPTIONS HTTP verb."""
        return Response(headers={"Allow": ", ".join(self.__methods__)})


Callable = typing.TypeVar("Callable", bound=typing.Callable)


def create_model_config(title: str = None, description: str = None):
    class ExclusiveModelConfig:
        @staticmethod
        def schema_extra(schema, model) -> None:
            if title is not None:
                schema["title"] = title
            if description is not None:
                schema["description"] = description

    return ExclusiveModelConfig


def parse_params(function: Callable) -> Callable:
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
            if isclass(annotation) and issubclass(annotation, BaseModel):
                model = annotation
            else:
                model = create_model(
                    "temporary_exclusive_model",
                    __config__=create_model_config(default.title, default.description),
                    __root__=(annotation, ...),
                )
            __parameters__[default.name] = model
            __exclusive_models__[model] = name
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


def _merge_multi_value(
    items: typing.List[typing.Tuple[str, str]]
) -> typing.Dict[str, typing.Union[str, typing.List[str]]]:
    """
    If there are values with the same key value, they are merged into a List.
    """
    return {
        k: v_list if len(v_list) > 1 else v_list[0]
        for k, v_list in (
            (k, list(v_iter))
            for k, v_iter in (
                lambda iterable, key: groupby(sorted(iterable, key=key), key=key)
            )(items, lambda kv: kv[0])
        )
    }


async def bound_params(handler: typing.Callable, request: Request) -> typing.Callable:
    """
    bound parameters "path", "query", "header", "cookie", "body" to the view function
    """
    parameters = getattr(handler, "__parameters__", None)
    request_body = getattr(handler, "__request_body__", None)
    exclusive_models = getattr(handler, "__exclusive_models__", {})
    if not (parameters or request_body):
        return handler

    data: typing.List[typing.Any] = []
    kwargs: typing.Dict[str, BaseModel] = {}

    try:
        # try to get parameters model and parse
        if parameters:
            if "path" in parameters:
                data.append(parameters["path"].parse_obj(request.path_params))

            if "query" in parameters:
                data.append(
                    parameters["query"].parse_obj(
                        _merge_multi_value(request.query_params.multi_items())
                    )
                )

            if "header" in parameters:
                data.append(
                    parameters["header"].parse_obj(
                        _merge_multi_value(request.headers.items())
                    )
                )

            if "cookie" in parameters:
                data.append(parameters["cookie"].parse_obj(request.cookies))

        # try to get body model and parse
        if request_body:
            _body_data = await request.data()
            if isinstance(_body_data, FormData):
                _body_data = _merge_multi_value(_body_data.multi_items())
            data.append(request_body.parse_obj(_body_data))

    except ValidationError as e:
        raise RequestValidationError(e)

    for _data in data:
        if _data.__class__.__name__ == "temporary_model":
            kwargs.update(_data.dict())
        elif _data.__class__.__name__ == "temporary_exclusive_model":
            kwargs[exclusive_models[_data.__class__]] = _data.__root__
        else:
            kwargs[exclusive_models[_data.__class__]] = _data
    return functools.partial(handler, **kwargs)
