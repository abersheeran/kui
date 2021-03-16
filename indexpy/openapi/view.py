from __future__ import annotations

import asyncio
import functools
from inspect import signature
from itertools import groupby
from typing import Any, Awaitable, Callable, Dict, List, Tuple, Type, TypeVar, Union

from baize.asgi import FormData
from pydantic import BaseModel, ValidationError, create_model

from indexpy.exceptions import RequestValidationError
from indexpy.requests import request
from indexpy.utils import safe_issubclass
from indexpy.views import HttpView

from .fields import FieldInfo


class ApiView(HttpView):
    def __init_subclass__(cls, /, **kwargs: Callable[[], Awaitable[Any]]) -> None:
        super().__init_subclass__(**kwargs)

        for function_name in (
            key for key in cls.HTTP_METHOD_NAMES if hasattr(cls, key)
        ):
            function = getattr(cls, function_name)
            if not asyncio.iscoroutinefunction(function):
                raise TypeError(
                    f"The function {function_name} should be defined using `async def`"
                )
            setattr(cls, function_name, parse_params(function))

    async def __impl__(self) -> Any:
        handler = getattr(self, request.method.lower(), self.http_method_not_allowed)
        handler = await bound_params(handler)
        return await handler()


CallableObject = TypeVar("CallableObject", bound=Callable)


def create_model_config(title: str = None, description: str = None):
    class ExclusiveModelConfig:
        @staticmethod
        def schema_extra(schema, model) -> None:
            if title is not None:
                schema["title"] = title
            if description is not None:
                schema["description"] = description

    return ExclusiveModelConfig


def parse_params(function: CallableObject) -> CallableObject:
    sig = signature(function)

    __parameters__: Dict[str, Any] = {
        "path": {},
        "query": {},
        "header": {},
        "cookie": {},
        "body": {},
    }
    __exclusive_models__ = {}

    for name, param in sig.parameters.items():
        default = param.default
        annotation = param.annotation

        if default == param.empty:
            continue

        if isinstance(default, FieldInfo) and getattr(default, "exclusive", False):
            if safe_issubclass(annotation, BaseModel):
                model = annotation
            else:
                model = create_model(
                    "temporary_exclusive_model",
                    __config__=create_model_config(default.title, default.description),
                    __root__=(annotation, ...),
                )
            __parameters__[default._in] = model
            __exclusive_models__[model] = name
            continue

        if safe_issubclass(__parameters__[default._in], BaseModel):
            raise RuntimeError(
                f"{default._in.capitalize()}(exclusive=True) "
                "and {default._in.capitalize()} cannot be used at the same time"
            )

        if annotation != param.empty:
            __parameters__[default._in][name] = (annotation, default)
        else:
            __parameters__[default._in][name] = default

    for key in (
        key
        for key in __parameters__
        if not safe_issubclass(__parameters__[key], BaseModel)
    ):
        __parameters__[key] = create_model("temporary_model", **__parameters__[key])  # type: ignore

    if "body" in __parameters__:
        setattr(function, "__request_body__", __parameters__.pop("body"))

    if __parameters__:
        setattr(function, "__parameters__", __parameters__)

    if __exclusive_models__:
        setattr(function, "__exclusive_models__", __exclusive_models__)

    return function


def _merge_multi_value(
    items: List[Tuple[str, str]]
) -> Dict[str, Union[str, List[str]]]:
    """
    If there are values with the same key value, they are merged into a List.
    """
    return {
        k: v_list if len(v_list) > 1 else v_list[0]
        for k, v_list in (
            (k, list(v for _, v in kv_iter))
            for k, kv_iter in (
                lambda iterable, key: groupby(sorted(iterable, key=key), key=key)
            )(items, lambda kv: kv[0])
        )
    }


async def bound_params(handler: Callable) -> Callable[[], Any]:
    """
    bound parameters "path", "query", "header", "cookie", "body" to the view function
    """
    parameters: Dict[str, BaseModel] = getattr(handler, "__parameters__", None)
    request_body: BaseModel = getattr(handler, "__request_body__", None)
    if not (parameters or request_body):
        return handler

    exclusive_models: Dict[Type[BaseModel], str] = getattr(
        handler, "__exclusive_models__", {}
    )

    data: List[Any] = []
    kwargs: Dict[str, BaseModel] = {}

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
