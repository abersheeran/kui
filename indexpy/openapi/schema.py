from copy import deepcopy
from typing import Any, List, Dict, Optional, Iterable, Union, Sequence

import yaml
from pydantic import BaseModel

from .types import File


def replace_definitions(schema: Dict[str, Any]) -> Dict[str, Any]:
    """
    replace $ref
    """
    schema = deepcopy(schema)

    if schema.get("definitions") is not None:

        def replace(value: Union[str, Sequence[Any], Dict[str, Any]]) -> None:
            if isinstance(value, str):
                return
            elif isinstance(value, Sequence):
                for _value in value:
                    replace(_value)
            elif isinstance(value, Dict):
                for _name in tuple(value.keys()):
                    if _name == "$ref":
                        define_schema = schema
                        for key in value["$ref"][2:].split("/"):
                            define_schema = define_schema[key]
                        # replace ref and del it
                        value.update(define_schema)
                        del value["$ref"]
                    elif isinstance(value[_name], Dict):
                        replace(value[_name])
                    elif isinstance(value[_name], Sequence):
                        for _value in value[_name]:
                            replace(_value)

        replace(schema["definitions"])
        replace(schema["properties"])
        del schema["definitions"]

    return schema


def schema_parameter(m: Optional[BaseModel], position: str) -> List[Dict[str, Any]]:
    """
    position: "path", "query", "header", "cookie"
    """
    result = []

    if m is not None:
        _schemas = replace_definitions(m.schema())
        properties: Dict[str, Any] = _schemas["properties"]
        _schemas["required"] = _schemas.get("required") or []

        for name, schema in properties.items():  # type: str, Dict[str, str]
            result.append(
                {
                    "in": position,
                    "name": name,
                    "description": schema.pop("description", ""),
                    "required": name in _schemas["required"],  # type: ignore
                    "schema": schema,
                }
            )
    return result


def schema_parameters(
    path: BaseModel = None,
    query: BaseModel = None,
    header: BaseModel = None,
    cookie: BaseModel = None,
) -> List[Dict[str, Any]]:

    return (
        schema_parameter(path, "path")
        + schema_parameter(query, "query")
        + schema_parameter(header, "header")
        + schema_parameter(cookie, "cookie")
    )


def schema_request_body(body: BaseModel = None) -> Optional[Dict[str, Any]]:
    if body is None:
        return None

    _schema = {"schema": replace_definitions(body.schema())}

    for field in body.__fields__.values():
        if issubclass(field.type_, File):
            return {
                "required": True,
                "content": {"multipart/form-data": _schema},
            }

    return {
        "required": True,
        "content": {"application/json": _schema},
    }


def schema_response(model: Union[BaseModel, str]) -> Dict[str, Any]:
    if isinstance(model, str):
        return yaml.safe_load(model.strip())
    return {"application/json": {"schema": replace_definitions(model.schema())}}
