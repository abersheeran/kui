from __future__ import annotations

from typing import Any

from baize.datastructures import UploadFile as _UploadFile
from pydantic import GetCoreSchemaHandler, GetJsonSchemaHandler
from pydantic_core import core_schema
from pydantic.json_schema import JsonSchemaValue


class UploadFile(_UploadFile):
    """
    wrap baize UploadFile
    """

    @classmethod
    def __get_validators__(cls):
        yield cls.validate

    @classmethod
    def __get_pydantic_core_schema__(
        cls, _source_type: Any, _handler: GetCoreSchemaHandler
    ) -> core_schema.CoreSchema:
        return core_schema.no_info_after_validator_function(
            cls.validate,
            core_schema.any_schema(),
        )

    @classmethod
    def __get_pydantic_json_schema__(
        cls, schema: core_schema.CoreSchema, handler: GetJsonSchemaHandler
    ) -> JsonSchemaValue:
        json_schema = handler(schema)
        json_schema.update(type="string", format="binary")
        return json_schema

    @classmethod
    def validate(cls, v):
        if not isinstance(v, _UploadFile):
            raise TypeError(
                f"Expected UploadFile, received {v.__class__.__name__} instead."
            )
        return v

    def __repr__(self):
        return f"File({self.filename})"
