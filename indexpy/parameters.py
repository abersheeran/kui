from __future__ import annotations

import functools
import inspect
from itertools import groupby
from typing import (
    Any,
    Awaitable,
    Callable,
    Dict,
    List,
    Optional,
    Sequence,
    Tuple,
    Type,
    TypeVar,
    Union,
)
from typing import cast as typing_cast

from baize.asgi import FormData
from pydantic import BaseConfig, BaseModel, ValidationError, create_model

from indexpy.exceptions import RequestValidationError
from indexpy.requests import request
from indexpy.utils import safe_issubclass

from .fields import FieldInfo, RequestInfo, Undefined

CallableObject = TypeVar("CallableObject", bound=Callable[..., Awaitable[Any]])


def create_model_config(title: str = None, description: str = None) -> Type[BaseConfig]:
    class ExclusiveModelConfig(BaseConfig):
        schema_extra = {
            k: v
            for k, v in {"title": title, "description": description}.items()
            if v is not None
        }

    return ExclusiveModelConfig


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


def create_new_callback(callback: CallableObject) -> CallableObject:
    sig = inspect.signature(callback)

    raw_parameters: Dict[str, Any] = {
        key: {} for key in ["path", "query", "header", "cookie", "body"]
    }
    exclusive_models: Dict[BaseModel, str] = {}

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
            raw_parameters[default._in] = model
            exclusive_models[model] = name
        else:
            if safe_issubclass(raw_parameters[default._in], BaseModel):
                raise RuntimeError(
                    f"{default._in.capitalize()}(exclusive=True) "
                    f"and {default._in.capitalize()} cannot be used at the same time"
                )
            if annotation == param.empty:
                annotation = Any
            raw_parameters[default._in][name] = (annotation, default)

    for key, params in filter(
        lambda kv: kv[1],
        ((key, raw_parameters.pop(key)) for key in tuple(raw_parameters.keys())),
    ):
        if safe_issubclass(params, BaseModel):
            model = params
        else:
            model = create_model("temporary_model", **params)
        raw_parameters[key] = model

    if "body" in raw_parameters:
        request_body: Optional[BaseModel] = raw_parameters.pop("body")
    else:
        request_body = None

    if raw_parameters:
        parameters: Optional[Dict[str, BaseModel]] = typing_cast(
            Dict[str, BaseModel], raw_parameters
        )
    else:
        parameters = None

    request_attrs: Dict[str, RequestInfo] = {
        name: param.default
        for name, param in sig.parameters.items()
        if isinstance(param.default, RequestInfo)
    }

    @functools.wraps(callback)
    async def callback_with_auto_bound_params(*args, **kwargs):
        if not (parameters or request_body or request_attrs):
            return await callback(*args, **kwargs)

        data: List[Any] = []
        keyword_params: Dict[str, Any] = {}

        # try to get parameters model and parse
        if parameters:
            if "path" in parameters:
                try:
                    data.append(parameters["path"].parse_obj(request.path_params))
                except ValidationError as e:
                    raise RequestValidationError(e, "path")

            if "query" in parameters:
                try:
                    data.append(
                        parameters["query"].parse_obj(
                            _merge_multi_value(request.query_params.multi_items())
                        )
                    )
                except ValidationError as e:
                    raise RequestValidationError(e, "query")

            if "header" in parameters:
                try:
                    data.append(parameters["header"].parse_obj(request.headers))
                except ValidationError as e:
                    raise RequestValidationError(e, "header")

            if "cookie" in parameters:
                try:
                    data.append(parameters["cookie"].parse_obj(request.cookies))
                except ValidationError as e:
                    raise RequestValidationError(e, "cookie")

        # try to get body model and parse
        if request_body:
            _body_data = await request.data()
            if isinstance(_body_data, FormData):
                _body_data = _merge_multi_value(_body_data.multi_items())
            try:
                data.append(request_body.parse_obj(_body_data))
            except ValidationError as e:
                raise RequestValidationError(e, "body")

        # try to get request instance attributes
        if request_attrs:
            for name, info in request_attrs.items():
                try:
                    value: Any = functools.reduce(
                        lambda attr, name: getattr(attr, name),
                        (info.alias or name).split("."),
                        request,
                    )
                except AttributeError:
                    if info.default is not Undefined:
                        value = info.default
                    elif info.default_factory is not None:
                        value = info.default_factory()
                    else:
                        raise
                keyword_params[name] = (
                    (await value) if inspect.isawaitable(value) else value
                )

        for _data in data:
            if _data.__class__.__name__ == "temporary_model":
                keyword_params.update(_data.dict())
            elif _data.__class__.__name__ == "temporary_exclusive_model":
                keyword_params[exclusive_models[_data.__class__]] = _data.__root__
            else:
                keyword_params[exclusive_models[_data.__class__]] = _data
        return await callback(*args, **{**keyword_params, **kwargs})  # type: ignore

    handler = callback_with_auto_bound_params

    if request_body is not None:
        __request_body__: List[BaseModel] = getattr(handler, "__request_body__", [])
        __request_body__.append(request_body)
        setattr(handler, "__request_body__", __request_body__)

    if parameters is not None:
        __parameters__: Dict[str, List[BaseModel]] = getattr(
            handler, "__parameters__", {}
        )
        for key, value in parameters.items():
            __parameters__.setdefault(key, []).append(value)
        setattr(handler, "__parameters__", __parameters__)

    __signature__ = inspect.Signature(
        parameters=[
            param
            for param in sig.parameters.values()
            if not isinstance(param.default, (FieldInfo, RequestInfo))
        ],
        return_annotation=sig.return_annotation,
    )
    setattr(callback_with_auto_bound_params, "__signature__", __signature__)

    return callback_with_auto_bound_params  # type: ignore


has_wrapped_by_auto_params = lambda function: (
    hasattr(function, "__parameters__") or hasattr(function, "__request_body__")
)


def auto_params(handler: CallableObject) -> CallableObject:
    if inspect.isclass(handler) and hasattr(handler, "__methods__"):
        for method in map(lambda x: x.lower(), handler.__methods__):  # type: ignore
            function = getattr(handler, method)
            if has_wrapped_by_auto_params(function):
                continue
            setattr(handler, method, create_new_callback(function))
        return handler
    elif inspect.iscoroutinefunction(handler):
        return create_new_callback(handler)
    else:
        return handler
