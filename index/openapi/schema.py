from copy import deepcopy
from typing import Any, List, Dict, Callable

from .models import Model


def _remove_info(schema: Dict[str, Any]) -> Dict[str, Any]:
    schema = deepcopy(schema)

    if schema.get("definitions") is not None:
        for _name, _property in schema["properties"].items():
            if "$ref" in _property:
                define_schema = schema
                for key in _property["$ref"][2:].split("/"):
                    define_schema = define_schema[key]
                schema["properties"][_name] = define_schema

        del schema["definitions"]

    return schema


def schema_parameters(
    path: Model = None, query: Model = None, header: Model = None, cookie: Model = None,
) -> List[Dict[str, Any]]:
    def schema_parameter(m: Model, position: str) -> List[Dict[str, Any]]:
        """
        position: "path", "query", "header", "cookie"
        """
        result = []

        if m:
            _schemas = _remove_info(m.schema())
            properties: Dict[str, Any] = _schemas["properties"]
            _schemas["required"] = _schemas.get("required") or []

            for name, schema in properties.items():
                result.append(
                    {
                        "in": position,
                        "name": name,
                        "description": schema.pop("description"),
                        "required": name in _schemas.get("required"),
                        "schema": schema,
                    }
                )
        return result

    return (
        schema_parameter(path, "path")
        + schema_parameter(query, "query")
        + schema_parameter(header, "header")
        + schema_parameter(cookie, "cookie")
    )


def schema_request_body(body: Model = None) -> Dict[str, Any]:
    if body is None:
        return

    return {
        "required": True,
        "content": {"application/json": {"schema": _remove_info(body.schema())}},
    }


def schema_response(model: Model) -> Dict[str, Any]:
    return {"application/json": {"schema": _remove_info(model.schema())}}
