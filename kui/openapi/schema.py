from __future__ import annotations

from typing import TYPE_CHECKING, Optional, Type, Union
from typing import cast as typing_cast

from baize.datastructures import ContentType
from pydantic import BaseModel
from typing_extensions import get_args, get_type_hints

from ..pydantic_compatible import get_model_fields, get_model_json_schema
from ..utils import safe_issubclass

if TYPE_CHECKING:
    from ..asgi import Kui as ASGIKui
    from ..wsgi import Kui as WSGIKui

from . import specification as spec
from .types import UploadFile


def _model_to_schema(model: Type[BaseModel]) -> spec.Schema:
    # Convert a Pydantic model to an OpenAPI schema and drop the top-level title for inline use.
    schema = get_model_json_schema(model)
    schema.pop("title")
    return typing_cast(spec.Schema, schema)


def schema_request_body(
    body: Type[BaseModel] | None, application: ASGIKui | WSGIKui
) -> Optional[spec.RequestBody]:
    if body is None:
        return None

    # Reuse the app data parser's declared content types by default, but force multipart/form-data when UploadFile is present.
    content_types = [
        str(v)
        for v in get_args(
            get_type_hints(application.factory_class.http.data, include_extras=True)[
                "return"
            ]
        )
        if isinstance(v, ContentType)
    ]

    for field in get_model_fields(body).values():
        if safe_issubclass(field.annotation, UploadFile):
            content_types = ["multipart/form-data"]

    return {
        "required": True,
        "content": {
            content_type: {"schema": _model_to_schema(body)}
            for content_type in content_types
        },
    }


def schema_response(content: Union[Type[BaseModel], spec.Schema]) -> spec.Schema:
    # Responses accept either a schema directly or a Pydantic model to convert here.
    if isinstance(content, dict):
        return content
    else:
        return _model_to_schema(content)
