from __future__ import annotations

from baize.datastructures import UploadFile as _UploadFile


class UploadFile(_UploadFile):
    """
    wrap starlette UploadFile for pydantic
    """

    @classmethod
    def __get_validators__(cls):
        yield cls.validate

    @classmethod
    def __modify_schema__(cls, field_schema):
        field_schema.update(type="string", format="binary")

    @classmethod
    def validate(cls, v):
        if not isinstance(v, UploadFile):
            raise TypeError("file required")
        return v

    def __repr__(self):
        return f"File({self.filename})"
