from copy import deepcopy
from typing import Any, Dict, List, Optional, Tuple, Type, Union

from pydantic import BaseModel

from indexpy.types import Literal

from .types import UploadFile


def schema_parameter(
    m: Optional[Type[BaseModel]],
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


def schema_request_body(body: Type[BaseModel] = None) -> Tuple[Optional[Dict], Dict]:
    if body is None:
        return None, {}

    _schema: Dict = deepcopy(body.schema())
    definitions = _schema.pop("definitions", {})
    content_type = "application/json"

    for field in body.__fields__.values():
        if issubclass(field.type_, UploadFile):
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
