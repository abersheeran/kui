from __future__ import annotations

import inspect
import sys
from copy import deepcopy
from typing import Any, Dict, List, Optional, Tuple, Type, Union

if sys.version_info[:2] < (3, 8):
    from typing_extensions import Literal
else:
    from typing import Literal

from pydantic import BaseModel

from .types import UploadFile


def schema_parameter(
    m: Optional[Type[BaseModel]],
    position: Literal["path", "query", "header", "cookie"],
) -> List[Dict[str, Any]]:

    if m is None:
        return []

    _schemas = deepcopy(m.schema())
    properties: Dict[str, Any] = _schemas["properties"]
    required = _schemas.get("required", ())

    return [
        {
            "in": position,
            "name": name,
            "description": schema.pop("description", ""),
            "required": name in required,  # type: ignore
            "schema": schema,
        }
        for name, schema in properties.items()
    ]


def schema_request_body(body: Type[BaseModel] = None) -> Tuple[Optional[Dict], Dict]:
    if body is None:
        return None, {}

    _schema: Dict = deepcopy(body.schema())
    definitions = _schema.pop("definitions", {})
    content_type = "application/json"

    for field in body.__fields__.values():
        if inspect.isclass(field.type_) and issubclass(field.type_, UploadFile):
            content_type = "multipart/form-data"

    return {
        "required": True,
        "content": {content_type: {"schema": _schema}},
    }, definitions


def schema_response(content: Union[Type[BaseModel], Dict]) -> Tuple[Dict, Dict]:
    if isinstance(content, dict):
        return content, {}
    schema = deepcopy(content.schema())
    definitions = schema.pop("definitions", {})
    return {"application/json": {"schema": schema}}, definitions
