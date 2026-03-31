from __future__ import annotations

import copy
import inspect
from typing import (
    TYPE_CHECKING,
    Any,
    Callable,
    Dict,
    List,
    Optional,
    Sequence,
    Set,
    Type,
)

from pydantic import BaseModel
from typing_extensions import Literal, get_args, get_type_hints

from ..pydantic_compatible import get_model_json_schema

if TYPE_CHECKING:
    from ..openapi import specification as spec


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
    # Aggregate OpenAPI metadata from the handler itself and from every dependency function.
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


def parse_docs_responses(callback):
    return [
        *getattr(callback, "__docs_responses__", []),
        *_get_response_docs(callback),
    ]
