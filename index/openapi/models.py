import os
import re
import copy
import typing
import asyncio
from abc import abstractmethod, ABCMeta

from aiofiles import open as asyncopen
from starlette.datastructures import UploadFile
from index.config import config

from .utils import merge_mapping


EMPTY_VALUE = ("", {}, [], None, ())

ALLOWS_TYPE = ("array", "boolean", "integer", "number", "object", "string")


class VerifyError(Exception):
    pass


class FieldVerifyError(VerifyError):
    def __init__(self, message: str) -> None:
        super().__init__(message)
        self.message = message


class ModelFieldVerifyError(FieldVerifyError):
    def __init__(self, message: typing.Dict[str, typing.Any]) -> None:
        super().__init__(message)
        self.message = message


class Field(metaclass=ABCMeta):
    def __init__(
        self,
        *,
        description: str = "",
        example: typing.Any = None,
        allow_null: bool = False,
        default: typing.Any = None,
    ):
        self.description = description
        self.example = example
        self.allow_null = allow_null
        self.default = default

    def check_null(self, value: typing.Any) -> typing.Any:
        if value is None:
            if callable(self.default):
                value = self.default()
            value = copy.deepcopy(self.default)

        if value in EMPTY_VALUE and not self.allow_null:
            raise FieldVerifyError("Not allowed to be empty.")
        return value

    @abstractmethod
    async def verify(self, value: typing.Any) -> typing.Any:
        """Verify and parse data into Python objects"""
        return self.check_null(value)

    @abstractmethod
    async def json(self, value: typing.Any) -> typing.Any:
        """parse data from Python objects"""

    def openapi(self) -> typing.Dict[str, typing.Any]:
        schema = {
            "description": self.description,
        }
        if self.default not in EMPTY_VALUE:
            schema["default"] = self.default
        return schema


class ModelMeta(type):
    def __init__(
        self,
        name: str,
        bases: typing.Iterable[typing.Any],
        namespace: typing.Dict[str, typing.Any],
    ):
        fields = {}
        for key, value in namespace.items():
            if isinstance(value, Field):
                fields[key] = value
        self.fields = fields
        super().__init__(name, bases, namespace)


class BaseModel(metaclass=ModelMeta):
    fields: typing.Dict[str, Field]


class ChoiceField(Field, metaclass=ABCMeta):
    def __init__(self, *, choices: typing.Iterable[str] = (), **kwargs):
        super().__init__(**kwargs)
        self.choices = choices
        if choices and self.default is not None:
            assert self.default in choices, "default value must be in choices"

    def check_choice(self, value: typing.Any) -> typing.Any:
        if self.choices and value not in self.choices:
            raise FieldVerifyError(f"value must be in {self.choices}")
        return value

    @abstractmethod
    async def verify(self, value: typing.Any) -> typing.Any:
        value = super().verify(value)
        value = self.check_choice(value)
        return value

    def openapi(self) -> typing.Dict[str, typing.Any]:
        schema = super().openapi()
        if self.choices:
            schema["enum"] = list(self.choices)
        return schema


class FileField(Field):
    def __init__(
        self,
        prefix: str,
        *,
        description: str = "",
        allow_null: bool = False,
        save: typing.Callable[[UploadFile], typing.Awaitable[str]] = None,
    ):
        super().__init__(description=description, allow_null=allow_null)
        self.prefix = prefix
        assert not prefix.startswith("/"), 'Prefix cannot start with "/".'
        if save is not None:
            setattr(self, "save", save)

    async def save(self, file: UploadFile) -> str:
        abspath = os.path.join(config.path, self.prefix, file.filename)
        if os.path.exists(abspath):
            raise FileExistsError(abspath)
        async with asyncopen(abspath, "w+") as target:
            while True:
                data = await file.read(1024)
                if not data:
                    break
                await target.write(data)
        return abspath

    async def verify(self, value: UploadFile) -> str:
        """return file path/url"""
        try:
            return await self.save(value)
        except FileExistsError:
            raise FieldVerifyError(f'This file "{value.filename}" already exists.')

    def json(self, value: typing.Any) -> typing.NoReturn:
        raise NotImplementedError("FileField not implement json")

    def openapi(self) -> typing.Dict[str, typing.Any]:
        schema = {"type": "string", "format": "binary"}
        if self.description:
            schema.update({"description": self.description})
        return schema


class BooleanField(Field):
    def __init__(self, *, default: typing.Any = None, **kwargs):
        assert default is None or default in (
            True,
            False,
        ), "default in BooleanField must be bool"
        kwargs["default"] = default
        super().__init__(**kwargs)

    def verify(self, value: typing.Any) -> bool:
        value = super().verify(value)
        return bool(value)

    def json(self, value: typing.Any) -> typing.Any:
        return bool(value)

    def openapi(self) -> typing.Dict[str, typing.Any]:
        schema = super().openapi()
        schema.update({"type": "boolean"})
        return schema


class IntField(ChoiceField):
    def verify(self, value: typing.Any) -> int:
        value = super().verify(value)
        try:
            return int(value)
        except ValueError:
            raise FieldVerifyError("Must be an integer.")

    def json(self, value: typing.Any) -> typing.Any:
        return int(value)

    def openapi(self) -> typing.Dict[str, typing.Any]:
        schema = super().openapi()
        schema.update({"type": "integer"})
        return schema


class FloatField(ChoiceField):
    def verify(self, value: typing.Any) -> float:
        value = super().verify(value)
        try:
            return float(value)
        except ValueError:
            raise FieldVerifyError("Must be an floating point number.")

    def json(self, value: typing.Any) -> typing.Any:
        return float(value)

    def openapi(self) -> typing.Dict[str, typing.Any]:
        schema = super().openapi()
        schema.update({"type": "number"})
        return schema


class StrField(ChoiceField):
    def verify(self, value: typing.Any) -> str:
        value = super().verify(value)
        return str(value)

    def json(self, value: typing.Any) -> typing.Any:
        return str(value)

    def openapi(self) -> typing.Dict[str, typing.Any]:
        schema = super().openapi()
        schema.update({"type": "string"})
        return schema


class EmailField(StrField):
    EMAIL_FORMAT = re.compile(r"(?P<name>\S+?)@(?P<domain>\S+?\.\S+?)")

    def check_format(self, value: str) -> str:
        if self.EMAIL_FORMAT.match(value) is None:
            raise FieldVerifyError("Must be a string in email format.")
        return value

    def verify(self, value: typing.Any) -> str:
        value = super().verify(value)
        return self.check_format(value)

    def openapi(self) -> typing.Dict[str, typing.Any]:
        schema = super().openapi()
        schema.update({"format": "email"})
        return schema


class ListField(Field):
    def __init__(self, field: Field, **kwargs):
        if "default" not in kwargs:
            kwargs["default"] = []
        assert isinstance(
            kwargs["default"], list
        ), "default in ListField must be `list`"
        super().__init__(**kwargs)
        self.field = field

    async def verify(self, value: typing.Iterable) -> typing.List[typing.Any]:
        result = []
        value = self.check_null(value)
        for each in value:
            data = self.field.verify(each)
            if asyncio.iscoroutine(data):
                data = await data
            result.append(data)
        return result

    def json(self, value: typing.Iterable) -> typing.List:
        return [self.field.json(item) for item in value]

    def openapi(self) -> typing.Dict[str, typing.Any]:
        schema = super().openapi()
        schema.update({"type": "array", "items": self.field.openapi()})
        return schema


class Model(BaseModel):
    content_type = "application/json"

    def __init__(
        self,
        raw_data: typing.Dict[str, typing.Any],
        *,
        default: typing.Dict[str, typing.Any] = None,
    ) -> None:
        if default:
            self.raw_data = merge_mapping(raw_data, default)
        else:
            self.raw_data = raw_data
        self.data: typing.Dict[str, typing.Any] = {}

    async def clean(self) -> typing.Dict[str, str]:
        errors = {}
        for name, field in self.fields.items():
            try:
                data = field.verify(self.raw_data.get(name))
                if asyncio.iscoroutine(data):
                    data = await data
                self.data[name] = data
                setattr(self, name, data)
            except FieldVerifyError as e:
                errors[name] = e.message
        return errors

    @classmethod
    async def serialization(
        cls, value: typing.Dict[str, typing.Any]
    ) -> typing.Dict[str, typing.Any]:
        result = {}
        for name, field in cls.fields.items():
            data = field.json(value.get(name))
            if asyncio.iscoroutine(data):
                data = await data
            result[name] = data
        return result


class ModelField(Field):
    def __init__(
        self, model: BaseModel, *, default: typing.Dict[str, typing.Any] = {}, **kwargs
    ):
        kwargs["default"] = None
        super().__init__(**kwargs)
        self.model = model
        self.default_model_value = default

    async def verify(self, value: typing.Any) -> typing.Any:
        model = self.model(value, default=self.default_model_value)
        errors = await model.clean()
        if errors:
            raise ModelFieldVerifyError(errors)
        return model

    async def json(self, value: typing.Any) -> typing.Any:
        return await self.model.serialization(value)

    def openapi(self) -> typing.Dict[str, typing.Any]:
        schema = super().openapi()
        schema.update(
            {
                "type": "object",
                "properties": {
                    name: field.openapi() for name, field in self.model.fields.items()
                },
            }
        )
        return schema
