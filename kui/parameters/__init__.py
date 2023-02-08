from __future__ import annotations

import copy
import functools
import inspect
from itertools import groupby
from typing import (
    TYPE_CHECKING,
    Any,
    Callable,
    Dict,
    List,
    Sequence,
    Tuple,
    Type,
    TypeVar,
    Union,
)
from typing import cast as typing_cast

from pydantic import BaseConfig, BaseModel, ValidationError, create_model
from typing_extensions import Annotated, get_args, get_origin, get_type_hints

if TYPE_CHECKING:
    from ..asgi import HttpRequest as ASGIHttpRequest
    from ..wsgi import HttpRequest as WSGIHttpRequest

from ..exceptions import RequestValidationError
from ..utils import safe_issubclass
from .fields import DependInfo, FieldInfo, RequestAttrInfo, Undefined

CallableObject = TypeVar("CallableObject", bound=Callable)


def create_model_config(
    title: str | None = None, description: str | None = None
) -> Type[BaseConfig]:
    class ExclusiveModelConfig(BaseConfig):
        schema_extra = {
            k: v
            for k, v in {"title": title, "description": description}.items()
            if v is not None
        }

    return ExclusiveModelConfig


sorted_groupby = lambda iterable, key: groupby(sorted(iterable, key=key), key=key)


def _merge_multi_value(
    items: Sequence[Tuple[str, Any]]
) -> Dict[str, Union[Any, List[Any]]]:
    """
    If there are values with the same key value, they are merged into a List.
    """
    return {
        k: v_list if len(v_list) > 1 else v_list[0]
        for k, v_list in (
            (k, [v for _, v in kv_iter])
            for k, kv_iter in sorted_groupby(items, lambda kv: kv[0])
        )
    }


def _parse_parameters_and_request_body_to_model(
    sig: inspect.Signature,
) -> Tuple[
    Dict[str, Type[BaseModel]] | None,
    Type[BaseModel] | None,
    Dict[Type[BaseModel], str],
]:
    raw_parameters: Dict[str, Any] = {
        key: {} for key in ["path", "query", "header", "cookie", "body"]
    }
    exclusive_models: Dict[Type[BaseModel], str] = {}

    for name, param in sig.parameters.items():
        if not (
            isinstance(param.default, FieldInfo)
            or (
                get_origin(param.annotation) is Annotated
                and isinstance(get_args(param.annotation)[1], FieldInfo)
            )
        ):
            continue

        if param.POSITIONAL_ONLY:
            raise TypeError(
                f"Parameter {name} cannot be defined as positional only parameters."
            )

        if isinstance(param.default, FieldInfo):
            type_ = param.annotation
            info = param.default
        else:
            type_, info = get_args(param.annotation)

        if getattr(info, "exclusive", False):
            if safe_issubclass(type_, BaseModel):
                model = type_
            else:
                model = create_model(
                    "temporary_exclusive_model",
                    __config__=create_model_config(info.title, info.description),
                    __root__=(type_, ...),
                )
            raw_parameters[info._in] = model
            exclusive_models[model] = name
        else:
            if safe_issubclass(raw_parameters[info._in], BaseModel):
                raise RuntimeError(
                    f"{info._in.capitalize()}(exclusive=True) "
                    f"and {info._in.capitalize()} cannot be used at the same time"
                )
            if type_ == param.empty:
                type_ = Any
            raw_parameters[info._in][name] = (type_, info)

    for key, params in filter(
        lambda kv: kv[1],
        ((key, raw_parameters.pop(key)) for key in tuple(raw_parameters.keys())),
    ):
        if safe_issubclass(params, BaseModel):
            model = params
        else:
            model = create_model("temporary_model", **params)  # type: ignore
        raw_parameters[key] = model

    request_body: Type[BaseModel] | None
    if "body" in raw_parameters:
        request_body = raw_parameters.pop("body")
    else:
        request_body = None

    parameters: Dict[str, Type[BaseModel]] | None
    if raw_parameters:
        parameters = typing_cast(Dict[str, Type[BaseModel]], raw_parameters)
    else:
        parameters = None

    return parameters, request_body, exclusive_models


def _parse_depends_attrs(sig: inspect.Signature) -> Dict[str, DependInfo]:
    return {
        **{
            name: param.default
            for name, param in sig.parameters.items()
            if isinstance(param.default, DependInfo)
        },
        **{
            name: get_args(param.annotation)[1]
            for name, param in sig.parameters.items()
            if get_origin(param.annotation) is Annotated
            and isinstance(get_args(param.annotation)[1], DependInfo)
        },
    }


def _parse_request_attrs(sig: inspect.Signature) -> Dict[str, RequestAttrInfo]:
    return {
        **{
            name: param.default
            for name, param in sig.parameters.items()
            if isinstance(param.default, RequestAttrInfo)
        },
        **{
            name: get_args(param.annotation)[1]
            for name, param in sig.parameters.items()
            if get_origin(param.annotation) is Annotated
            and isinstance(get_args(param.annotation)[1], RequestAttrInfo)
        },
    }


def _create_new_signature(sig: inspect.Signature) -> inspect.Signature:
    return inspect.Signature(
        parameters=[
            param
            for param in sig.parameters.values()
            if not (
                isinstance(param.default, (FieldInfo, RequestAttrInfo, DependInfo))
                or (
                    get_origin(param.annotation) is Annotated
                    and isinstance(
                        get_args(param.annotation)[1], (FieldInfo, RequestAttrInfo)
                    )
                )
            )
        ],
        return_annotation=sig.return_annotation,
    )


def _get_response_docs(handler: Callable[..., Any]) -> List[Dict[Any, Any]]:
    response_docs: List[Dict[Any, Any]] = []
    for response in get_args(
        (
            get_type_hints(handler.__call__, include_extras=True)  # type: ignore
            if (
                callable(handler)
                and not (inspect.isfunction(handler) or inspect.ismethod(handler))
            )
            else get_type_hints(handler, include_extras=True)
        ).get("return")
    ):
        if isinstance(response, dict):
            response_docs.append(response)
    return copy.deepcopy(response_docs)


def _update_docs(
    old_handler: Callable[..., Any],
    handler: Callable[..., Any],
    parameters: Dict[str, Type[BaseModel]] | None,
    request_body: Type[BaseModel] | None,
    depend_functions: Dict[str, Callable[..., Any]],
) -> None:
    if request_body is not None:
        __request_body__: List[Type[BaseModel]] = getattr(
            handler, "__docs_request_body__", []
        )
        __request_body__.append(request_body)
        setattr(handler, "__docs_request_body__", __request_body__)

    if parameters is not None:
        __parameters__: Dict[str, List[Type[BaseModel]]] = getattr(
            handler, "__docs_parameters__", {}
        )
        for key, parameter_model in parameters.items():
            __parameters__.setdefault(key, []).append(parameter_model)
        setattr(handler, "__docs_parameters__", __parameters__)

    for func in depend_functions.values():
        __request_body__ = getattr(handler, "__docs_request_body__", [])
        __request_body__.extend(getattr(func, "__docs_request_body__", []))
        setattr(handler, "__docs_request_body__", __request_body__)

        __parameters__ = getattr(handler, "__docs_parameters__", {})
        for key, value in getattr(func, "__docs_parameters__", {}).items():
            __parameters__.setdefault(key, []).extend(value)
        setattr(handler, "__docs_parameters__", __parameters__)

        __responses__: List[Dict[Any, Any]] = getattr(handler, "__docs_responses__", [])
        __responses__.extend(_get_response_docs(func))
        setattr(handler, "__docs_responses__", __responses__)


def _validate_parameters(
    parameters: Dict[str, Type[BaseModel]], request: ASGIHttpRequest | WSGIHttpRequest
) -> List[BaseModel]:
    data = []

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

    return data


def _validate_request_attr(
    request_attrs: Dict[str, RequestAttrInfo],
    request: ASGIHttpRequest | WSGIHttpRequest,
) -> Dict[str, Any]:
    result = {}
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
        result[name] = value
    return result


def _convert_model_data_to_keyword_arguments(
    data: List[BaseModel], exclusive_models: Dict[Type[BaseModel], str]
) -> Dict[str, Any]:
    result = {}
    for _data in data:
        if _data.__class__.__name__ == "temporary_model":
            result.update(
                {name: getattr(_data, name) for name in _data.__fields__.keys()}
            )
        elif _data.__class__.__name__ == "temporary_exclusive_model":
            result[exclusive_models[_data.__class__]] = _data.__root__  # type: ignore
        else:
            result[exclusive_models[_data.__class__]] = _data
    return result


def _create_new_class(cls):
    """
    Create a fake class for auto-bound parameters.
    """

    @functools.wraps(cls, updated=())
    class NewClass(cls):
        pass

    return NewClass


def create_auto_params(
    create_new_callback: Callable[[CallableObject], CallableObject]
) -> Callable[[CallableObject], CallableObject]:
    """
    Create auto_params
    """

    def auto_params(handler: CallableObject) -> CallableObject:
        if hasattr(handler, "__methods__"):
            new_class = _create_new_class(handler)
            for method in map(lambda x: x.lower(), handler.__methods__):  # type: ignore
                old_callback = getattr(handler, method)
                new_callback = create_new_callback(old_callback)
                setattr(new_class, method, new_callback)  # note: set to new class
                setattr(
                    new_callback,
                    "__docs_responses__",
                    parse_docs_responses(old_callback),
                )
            setattr(new_class, "__raw_handler__", handler)
            return new_class
        else:
            old_callback = handler
            new_callback = create_new_callback(old_callback)
            setattr(
                new_callback, "__docs_responses__", parse_docs_responses(old_callback)
            )
            setattr(new_callback, "__raw_handler__", handler)
            return new_callback  # type: ignore

    return auto_params


def update_wrapper(
    new_handler: CallableObject, old_handler: Callable
) -> CallableObject:
    """
    Update wrapper for auto-bound parameters.
    """
    for attr in dir(old_handler):
        if attr.startswith("__docs_") or attr in ("__method__", "__methods__"):
            setattr(new_handler, attr, getattr(old_handler, attr))

    return new_handler


def parse_docs_responses(callback):
    return [
        *getattr(callback, "__docs_responses__", []),
        *_get_response_docs(callback),
    ]
