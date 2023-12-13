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
    Optional,
    Sequence,
    Set,
    Tuple,
    Type,
    TypeVar,
    Union,
)
from typing import cast as typing_cast

from pydantic import BaseModel, ValidationError, create_model
from pydantic.fields import FieldInfo
from typing_extensions import Annotated, Literal, get_args, get_origin, get_type_hints

from ..pydantic_compatible import (
    create_root_model,
    get_model_fields,
    get_model_json_schema,
    validate_model,
)

if TYPE_CHECKING:
    from ..asgi import HttpRequest as ASGIHttpRequest
    from ..openapi import specification as spec
    from ..wsgi import HttpRequest as WSGIHttpRequest

from ..exceptions import RequestValidationError
from ..utils import safe_issubclass
from .fields import (
    BaseHTTPFieldInfo,
    Depends,
    InBody,
    InCookie,
    InHeader,
    InPath,
    InQuery,
)

CallableObject = TypeVar("CallableObject", bound=Callable)


get_annotated_args = lambda tp: [
    j
    for i in (
        (get_annotated_args(t) if get_origin(t) is Annotated else [t])  # type: ignore
        for t in get_args(tp)
    )
    for j in i
]

sorted_groupby = lambda iterable, key: groupby(sorted(iterable, key=key), key=key)


def _merge_multi_value(
    items: Sequence[Tuple[str, Any]],
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
    Dict[Literal["path", "query", "header", "cookie"], Type[BaseModel]] | None,
    Type[BaseModel] | None,
    Dict[Type[BaseModel], str],
    Dict[Literal["path", "query", "header", "cookie"], Dict[str, Any]],
]:
    raw_parameters: Dict[str, Any] = {
        key: {} for key in ["path", "query", "header", "cookie", "body"]
    }
    exclusive_models: Dict[Type[BaseModel], str] = {}
    security_info: Dict[
        Literal["path", "query", "header", "cookie"], Dict[str, Any]
    ] = {"path": {}, "query": {}, "header": {}, "cookie": {}}

    for name, param in sig.parameters.items():
        if not (
            get_origin(param.default) is Annotated
            or get_origin(param.annotation) is Annotated
        ):
            continue

        if param.POSITIONAL_ONLY:
            raise TypeError(
                f"Parameter {name} cannot be defined as positional only parameters."
            )

        if get_origin(param.default) is Annotated:
            raise RuntimeError(
                f"Parameter {name} default value cannot be defined as {param.default}."
            )

        type_, *annontated_list = get_annotated_args(param.annotation)
        kui_field: Union[InPath, InQuery, InHeader, InCookie, InBody]
        for kui_field in filter(
            lambda x: isinstance(x, (InPath, InQuery, InHeader, InCookie, InBody)),
            annontated_list,
        ):
            break
        else:
            # If there is no kui field, skip it.
            continue

        if kui_field.exclusive:
            model = create_root_model(type_)
            raw_parameters[kui_field._in] = model
            exclusive_models[model] = name
        else:
            if safe_issubclass(raw_parameters[kui_field._in], BaseModel):
                raise RuntimeError(
                    f"{kui_field._in.capitalize()}(exclusive=True) "
                    f"and {kui_field._in.capitalize()} cannot be used at the same time"
                )
            field_info = next(
                filter(lambda x: isinstance(x, FieldInfo), annontated_list)
            )
            raw_parameters[kui_field._in][name] = (type_, field_info)
            if (
                isinstance(kui_field, (InQuery, InHeader, InCookie))
                and kui_field.security
            ):
                security_info[kui_field._in][
                    field_info.alias or name
                ] = kui_field.security

    for key, params in filter(
        lambda kv: kv[1],
        ((key, raw_parameters.pop(key)) for key in tuple(raw_parameters.keys())),
    ):
        if safe_issubclass(params, BaseModel):
            model = params
        else:
            model = create_model("temporary_model", **params)
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

    return (
        typing_cast(
            Dict[Literal["path", "query", "header", "cookie"], Type[BaseModel]],
            parameters,
        ),
        request_body,
        exclusive_models,
        security_info,
    )


def _parse_depends_attrs(sig: inspect.Signature) -> Dict[str, Depends]:
    if {
        name: param.default
        for name, param in sig.parameters.items()
        if isinstance(param.default, Depends)
    }:
        raise RuntimeError("Depends cannot be used as default value of parameters.")

    return {
        name: get_args(param.annotation)[1]
        for name, param in sig.parameters.items()
        if get_origin(param.annotation) is Annotated
        and isinstance(get_args(param.annotation)[1], Depends)
    }


def _create_new_signature(sig: inspect.Signature) -> inspect.Signature:
    return inspect.Signature(
        parameters=[
            param
            for param in sig.parameters.values()
            if not (
                isinstance(param.default, (BaseHTTPFieldInfo, Depends))
                or (
                    get_origin(param.annotation) is Annotated
                    and isinstance(get_args(param.annotation)[1], FieldInfo)
                )
            )
        ],
        return_annotation=sig.return_annotation,
    )


def _get_parameters_docs(
    m: Optional[Type[BaseModel]],
    position: Literal["path", "query", "header", "cookie"],
    security_fields: Set[str],
) -> List[spec.Parameter]:
    if m is None:
        return []

    _schemas: Dict[str, Any] = get_model_json_schema(m)
    properties: Dict[str, Any] = _schemas["properties"]
    required: Sequence[str] = _schemas.get("required", ())

    return [
        {
            "in": position,
            "name": name,
            "description": schema.pop("description", ""),
            "required": name in required,
            "schema": schema,
            "deprecated": schema.pop("deprecated", False),
        }
        for name, schema in properties.items()
        if name not in security_fields
    ]


def _merge_parameters_docs(
    x: List[spec.Parameter], y: List[spec.Parameter]
) -> List[spec.Parameter]:
    result = x + [
        param
        for param in y
        if not any(
            map(
                lambda x_param: (
                    x_param["name"] == param["name"] and x_param["in"] == param["in"]
                ),
                x,
            )
        )
    ]
    return result


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
    parameters: Dict[Literal["path", "query", "header", "cookie"], Type[BaseModel]]
    | None,
    request_body: Type[BaseModel] | None,
    depend_functions: Dict[str, Callable[..., Any]],
    security_info: Dict[Literal["path", "query", "header", "cookie"], Dict[str, Any]],
) -> None:
    if inspect.ismethod(handler):
        handler = handler.__func__  # type: ignore

    if isinstance(handler.__doc__, str):
        clean_doc = inspect.cleandoc(handler.__doc__)
        if not hasattr(handler, "__docs_summary__") and not hasattr(
            handler, "__docs_description__"
        ):
            for k, value in zip(("summary", "description"), clean_doc.split("\n\n", 1)):
                setattr(handler, f"__docs_{k}__", value)
        elif not hasattr(handler, "__docs_description__"):
            setattr(handler, "__docs_description__", clean_doc)

    if request_body is not None:
        __request_body__: List[Type[BaseModel]] = getattr(
            handler, "__docs_request_body__", []
        )
        __request_body__.append(request_body)
        setattr(handler, "__docs_request_body__", __request_body__)

    if parameters is not None:
        __parameters__: List[Any] = getattr(handler, "__docs_parameters__", [])
        __security__: List[Any] = getattr(handler, "__docs_security__", [])
        for position, model in parameters.items():
            __parameters__ = _merge_parameters_docs(
                __parameters__,
                _get_parameters_docs(
                    model, position, set(security_info[position].keys())
                ),
            )
        __security__.extend(info for p in security_info.values() for info in p.values())
        setattr(handler, "__docs_security__", __security__)
        setattr(handler, "__docs_parameters__", __parameters__)

    setattr(handler, "__docs_responses__", parse_docs_responses(old_handler))

    for func in depend_functions.values():
        __request_body__ = getattr(handler, "__docs_request_body__", [])
        __request_body__.extend(getattr(func, "__docs_request_body__", []))
        setattr(handler, "__docs_request_body__", __request_body__)

        setattr(
            handler,
            "__docs_parameters__",
            _merge_parameters_docs(
                getattr(handler, "__docs_parameters__", []),
                getattr(func, "__docs_parameters__", []),
            ),
        )

        __security__ = getattr(handler, "__docs_security__", [])
        __security__.extend(getattr(func, "__docs_security__", []))
        setattr(handler, "__docs_security__", __security__)

        __responses__: List[Dict[Any, Any]] = getattr(handler, "__docs_responses__", [])
        __responses__.extend(_get_response_docs(func))
        setattr(handler, "__docs_responses__", __responses__)


def _validate_parameters(
    parameters: Dict[Literal["path", "query", "header", "cookie"], Type[BaseModel]],
    request: ASGIHttpRequest | WSGIHttpRequest,
) -> List[Tuple[Type[BaseModel], Any]]:
    data = []

    if "path" in parameters:
        try:
            data.append(validate_model(parameters["path"], request.path_params))
        except ValidationError as e:
            raise RequestValidationError(e, "path")

    if "query" in parameters:
        try:
            data.append(
                validate_model(
                    parameters["query"],
                    _merge_multi_value(request.query_params.multi_items()),
                )
            )
        except ValidationError as e:
            raise RequestValidationError(e, "query")

    if "header" in parameters:
        try:
            data.append(validate_model(parameters["header"], request.headers._dict))
        except ValidationError as e:
            raise RequestValidationError(e, "header")

    if "cookie" in parameters:
        try:
            data.append(validate_model(parameters["cookie"], request.cookies))
        except ValidationError as e:
            raise RequestValidationError(e, "cookie")

    return data


def _convert_model_data_to_keyword_arguments(
    data: List[Tuple[Type[BaseModel], Any]],
    exclusive_models: Dict[Type[BaseModel], str],
) -> Dict[str, Any]:
    result = {}
    for model, value in data:
        if model.__name__ == "temporary_model":
            result.update(value)
        else:
            result[exclusive_models[model]] = value
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
    create_new_callback: Callable[[CallableObject], CallableObject],
) -> Callable[[CallableObject], CallableObject]:
    """
    Create auto_params
    """

    def auto_params(handler: CallableObject) -> CallableObject:
        if hasattr(handler, "__methods__"):
            new_class = _create_new_class(handler)
            for method in map(lambda x: x.lower(), handler.__methods__):
                old_callback = getattr(handler, method)
                new_callback = create_new_callback(old_callback)
                setattr(new_class, method, new_callback)  # note: set to new class
            setattr(
                new_class,
                "__raw_handler__",
                getattr(handler, "__raw_handler__", handler),
            )
            return new_class
        else:
            old_callback = handler
            new_callback = create_new_callback(old_callback)
            setattr(
                new_callback,
                "__raw_handler__",
                getattr(handler, "__raw_handler__", handler),
            )
            return new_callback

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

    setattr(new_handler, "__raw_handler__", old_handler)

    return new_handler


def parse_docs_responses(callback):
    return [
        *getattr(callback, "__docs_responses__", []),
        *_get_response_docs(callback),
    ]
