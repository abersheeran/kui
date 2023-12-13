from __future__ import annotations

from typing import Any

from baize.datastructures import UploadFile as _UploadFile

from ..pydantic_compatible import IS_V1

if IS_V1:

    class UploadFile(_UploadFile):  # type: ignore
        """
        wrap baize UploadFile
        """

        @classmethod
        def validate(cls, v):
            if not isinstance(v, _UploadFile):
                raise TypeError(
                    f"Expected UploadFile, received {v.__class__.__name__} instead."
                )
            return v

        def __repr__(self):
            return f"File({self.filename})"

        @classmethod
        def __get_validators__(cls):
            yield cls.validate

        @classmethod
        def __modify_schema__(cls, field_schema):
            field_schema.update(type="string", format="binary")


else:
    from pydantic import GetCoreSchemaHandler, GetJsonSchemaHandler
    from pydantic.json_schema import JsonSchemaValue
    from pydantic_core.core_schema import (
        CoreSchema,
        any_schema,
        no_info_after_validator_function,
    )

    class UploadFile(_UploadFile):  # type: ignore
        """
        wrap baize UploadFile
        """

        @classmethod
        def validate(cls, v):
            if not isinstance(v, _UploadFile):
                raise TypeError(
                    f"Expected UploadFile, received {v.__class__.__name__} instead."
                )
            return v

        def __repr__(self):
            return f"File({self.filename})"

        @classmethod
        def __get_pydantic_core_schema__(
            cls, _source_type: Any, _handler: GetCoreSchemaHandler
        ) -> CoreSchema:
            return no_info_after_validator_function(cls.validate, any_schema())

        @classmethod
        def __get_pydantic_json_schema__(
            cls, schema: CoreSchema, handler: GetJsonSchemaHandler
        ) -> JsonSchemaValue:
            json_schema = handler(schema)
            json_schema.update(type="string", format="binary")
            return json_schema
