import copy
from typing import Any, Dict, Tuple, Type

from pydantic import BaseModel
from pydantic import __version__ as pydantic_version

IS_V1 = pydantic_version.startswith("1.")

REF_TEMPLATE = "#/components/schemas/{model}"

__all__ = [
    "IS_V1",
    "validate_model",
    "get_model_fields",
    "get_model_json_schema",
    "create_root_model",
    "Undefined",
    "to_jsonable_python",
]

if IS_V1:
    from pydantic import create_model
    from pydantic.fields import ModelField, Undefined  # type: ignore
    from pydantic.json import pydantic_encoder as to_jsonable_python

    DEFINITIONS_KEY = "definitions"

    def validate_model(model: Type[BaseModel], v: Any) -> Tuple[Type[BaseModel], Any]:
        res = model.parse_obj(v)
        if hasattr(res, "__root__"):
            return model, res.__root__
        else:
            return model, res.dict(by_alias=False)

    def get_model_fields(model: Type[BaseModel]) -> Dict[str, ModelField]:  # type: ignore
        return model.__fields__  # type: ignore

    def get_model_json_schema(model: Type[BaseModel]) -> Dict[str, str]:
        return copy.deepcopy(model.schema(ref_template=REF_TEMPLATE))

    def create_root_model(type_: Any) -> Type[BaseModel]:
        return create_model("RootModel", __root__=(type_, ...))
else:
    from pydantic import RootModel
    from pydantic.fields import FieldInfo
    from pydantic_core import PydanticUndefined as Undefined
    from pydantic_core import to_jsonable_python

    DEFINITIONS_KEY = "$defs"

    def validate_model(model: Type[BaseModel], v: Any) -> Tuple[Type[BaseModel], Any]:
        res = model.model_validate(v)
        if isinstance(res, RootModel):
            return model, res.root
        else:
            return model, res.model_dump(by_alias=False)

    def get_model_fields(model: Type[BaseModel]) -> Dict[str, FieldInfo]:  # type: ignore
        return model.model_fields

    def get_model_json_schema(model: Type[BaseModel]) -> Dict[str, str]:
        return copy.deepcopy(model.model_json_schema(ref_template=REF_TEMPLATE))

    def create_root_model(type_: Any) -> Type[BaseModel]:
        return RootModel[type_]
