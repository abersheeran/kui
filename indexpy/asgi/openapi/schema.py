from __future__ import annotations

import inspect
from copy import deepcopy
from typing import Any, Dict, List, Optional, Tuple, Type, Union
from typing import cast as typing_cast

from baize.datastructures import ContentType
from pydantic import BaseModel
from typing_extensions import Literal, get_args, get_type_hints

from .. import request
from . import specification as spec
from .types import UploadFile

REF_TEMPLATE = "#/components/schemas/{model}"


def schema_parameter(
    m: Optional[Type[BaseModel]],
    position: Literal["path", "query", "header", "cookie"],
) -> List[spec.Parameter]:

    if m is None:
        return []

    _schemas = deepcopy(m.schema(ref_template=REF_TEMPLATE))
    properties: Dict[str, Any] = _schemas["properties"]
    required = _schemas.get("required", ())

    return [
        {
            "in": position,
            "name": name,
            "description": schema.pop("description", ""),
            "required": name in required,  # type: ignore
            "schema": schema,
            "deprecated": schema.pop("deprecated", False),
        }
        for name, schema in properties.items()
    ]


def schema_request_body(
    body: Type[BaseModel] = None,
) -> Tuple[Optional[spec.RequestBody], dict]:
    if body is None:
        return None, {}

    schema: Dict = deepcopy(body.schema(ref_template=REF_TEMPLATE))
    schema.pop("title")
    definitions = schema.pop("definitions", {})
    content_types = [
        str(v)
        for v in get_args(get_type_hints(request.data, include_extras=True)["return"])
        if isinstance(v, ContentType)
    ]

    for field in body.__fields__.values():
        if inspect.isclass(field.type_) and issubclass(field.type_, UploadFile):
            content_types = ["multipart/form-data"]

    return {
        "required": True,
        "content": {
            content_type: {"schema": deepcopy(schema)} for content_type in content_types
        },
    }, definitions


def schema_response(
    content: Union[Type[BaseModel], Dict[str, spec.MediaType]]
) -> Tuple[Dict[str, spec.MediaType], dict]:
    if isinstance(content, dict):
        return content, {}
    schema = deepcopy(content.schema(ref_template=REF_TEMPLATE))
    schema.pop("title")
    definitions = schema.pop("definitions", {})
    return {
        "application/json": {"schema": typing_cast(spec.Schema, schema)}
    }, definitions
