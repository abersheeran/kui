from copy import deepcopy
from typing import Any, Dict, List, Tuple, Optional, Union

import yaml
from pydantic import BaseModel

from ..types import Literal
from .types import File


def schema_parameter(
    m: Optional[BaseModel],
    position: Literal["path", "query", "header", "cookie"],
) -> List[Dict[str, Any]]:
    result = []

    if m is not None:
        _schemas = deepcopy(m.schema())
        properties: Dict[str, Any] = _schemas["properties"]
        required = _schemas.get("required", ())

        for name, schema in properties.items():  # type: str, Dict[str, str]
            result.append(
                {
                    "in": position,
                    "name": name,
                    "description": schema.pop("description", ""),
                    "required": name in required,  # type: ignore
                    "schema": schema,
                }
            )
    return result


def schema_request_body(body: BaseModel = None) -> Tuple[Optional[Dict], Dict]:
    if body is None:
        return None, {}

    _schema: Dict = deepcopy(body.schema())
    definitions = _schema.pop("definitions", {})

    for field in body.__fields__.values():
        if issubclass(field.type_, File):
            return {
                "required": True,
                "content": {"multipart/form-data": {"schema": _schema}},
            }, definitions

    return {
        "required": True,
        "content": {"application/json": {"schema": _schema}},
    }, definitions


def schema_response(model: Union[BaseModel, str]) -> Tuple[Dict, Dict]:
    if isinstance(model, str):
        return yaml.safe_load(model.strip()), {}
    schema = deepcopy(model.schema())
    definitions = schema.pop("definitions", {})
    return {"application/json": {"schema": schema}}, definitions
