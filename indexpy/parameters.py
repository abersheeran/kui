from __future__ import annotations

import copy
import functools
import inspect
from itertools import groupby
from typing import Any, Callable, Dict, List, Sequence, Tuple, Type, TypeVar, Union

from baize.asgi import FormData
from pydantic import BaseConfig, BaseModel, ValidationError, create_model

from indexpy.exceptions import RequestValidationError
from indexpy.requests import request
from indexpy.utils import safe_issubclass

from .fields import FieldInfo, RequestInfo

CallableObject = TypeVar("CallableObject", bound=Callable)


def create_model_config(title: str = None, description: str = None) -> Type[BaseConfig]:
    class ExclusiveModelConfig(BaseConfig):
        schema_extra = {
            k: v
            for k, v in {"title": title, "description": description}.items()
            if v is not None
        }

    return ExclusiveModelConfig


def parse_signature(function: CallableObject) -> CallableObject:
    sig = inspect.signature(function)

    __parameters__: Dict[str, Any] = {
        key: {} for key in ["path", "query", "header", "cookie", "body"]
    }
    __exclusive_models__: Dict[BaseModel, str] = {}

    for name, param in sig.parameters.items():
        if not isinstance(param.default, FieldInfo):
            continue

        if param.POSITIONAL_ONLY:
            raise TypeError(
                f"Parameter {name} cannot be defined as positional only parameters."
            )

        default = param.default
        annotation = param.annotation

        if getattr(default, "exclusive", False):
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
        else:
            if safe_issubclass(__parameters__[default._in], BaseModel):
                raise RuntimeError(
                    f"{default._in.capitalize()}(exclusive=True) "
                    f"and {default._in.capitalize()} cannot be used at the same time"
                )
            if annotation == param.empty:
                annotation = Any
            __parameters__[default._in][name] = (annotation, default)

    for key, params in filter(
        lambda kv: kv[1],
        ((key, __parameters__.pop(key)) for key in tuple(__parameters__.keys())),
    ):
        if safe_issubclass(params, BaseModel):
            model = params
        else:
            model = create_model("temporary_model", **params)
        __parameters__[key] = model

    if "body" in __parameters__:
        setattr(function, "__request_body__", __parameters__.pop("body"))

    if __parameters__:
        setattr(function, "__parameters__", __parameters__)

    if __exclusive_models__:
        setattr(function, "__exclusive_models__", __exclusive_models__)

    request_attrs = {
        name: param.default
        for name, param in sig.parameters.items()
        if isinstance(param.default, RequestInfo)
    }
    if request_attrs:
        setattr(function, "__request_attrs__", request_attrs)

    __signature__ = inspect.Signature(
        parameters=[
            param
            for param in sig.parameters.values()
            if (
                not isinstance(param.default, FieldInfo)
                or not isinstance(param.default, RequestInfo)
            )
        ],
        return_annotation=sig.return_annotation,
    )
    setattr(function, "__signature__", __signature__)

    return function


def _merge_multi_value(
    items: Sequence[Tuple[str, Any]]
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


async def verify_params(handler: CallableObject) -> CallableObject:
    parameters: Dict[str, BaseModel] = getattr(handler, "__parameters__", None)
    request_body: BaseModel = getattr(handler, "__request_body__", None)
    request_attrs: Dict[str, RequestInfo] = getattr(handler, "__request_attrs__", None)
    if not (parameters or request_body or request_attrs):
        return handler

    exclusive_models: Dict[Type[BaseModel], str] = getattr(
        handler, "__exclusive_models__", {}
    )

    data: List[Any] = []
    kwargs: Dict[str, Any] = {}

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
                data.append(parameters["header"].parse_obj(request.headers))

            if "cookie" in parameters:
                data.append(parameters["cookie"].parse_obj(request.cookies))

        # try to get body model and parse
        if request_body:
            _body_data = await request.data()
            if isinstance(_body_data, FormData):
                _body_data = _merge_multi_value(_body_data.multi_items())
            data.append(request_body.parse_obj(_body_data))

        # try to get request instance attributes
        if request_attrs:
            for name, info in request_attrs.items():
                value: Any = functools.reduce(
                    lambda attr, name: getattr(attr, name),
                    (info.alias or name).split("."),
                    request,
                )
                kwargs[name] = (await value) if inspect.isawaitable(value) else value

    except ValidationError as e:
        raise RequestValidationError(e)

    for _data in data:
        if _data.__class__.__name__ == "temporary_model":
            kwargs.update(_data.dict())
        elif _data.__class__.__name__ == "temporary_exclusive_model":
            kwargs[exclusive_models[_data.__class__]] = _data.__root__
        else:
            kwargs[exclusive_models[_data.__class__]] = _data
    return functools.partial(handler, **kwargs)  # type: ignore


def create_new_callback(callback: CallableObject) -> CallableObject:
    @functools.wraps(callback)
    async def callback_with_auto_bound_params(*args, **kwargs):
        p = await verify_params(callback)
        return await p(*args, **kwargs)

    return callback_with_auto_bound_params  # type: ignore


def auto_params(handler: CallableObject) -> CallableObject:
    if inspect.isclass(handler) and hasattr(handler, "__methods__"):
        handler = copy.deepcopy(handler)
        for method in map(lambda x: x.lower(), handler.__methods__):  # type: ignore
            callback = parse_signature(getattr(handler, method))
            setattr(handler, method, create_new_callback(callback))
        return handler
    elif inspect.iscoroutinefunction(handler):
        handler = copy.deepcopy(handler)
        callback = parse_signature(handler)
        return create_new_callback(callback)
    else:
        return handler
