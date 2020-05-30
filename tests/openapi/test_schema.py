from typing import Union, List

from indexpy.openapi.schema import replace_definitions
from pydantic import BaseModel


def test_schema_models():
    class Foo(BaseModel):
        foo: int

    class Bar(BaseModel):
        bar: str

    class A(BaseModel):
        a: Foo

    class B(BaseModel):
        b: Union[Foo, Bar]

    class C(BaseModel):
        c: List[Foo]

    assert replace_definitions(A.schema()) == {
        "title": "A",
        "type": "object",
        "properties": {
            "a": {
                "title": "Foo",
                "type": "object",
                "properties": {"foo": {"title": "Foo", "type": "integer"}},
                "required": ["foo"],
            }
        },
        "required": ["a"],
    }
    assert replace_definitions(B.schema()) == {
        "title": "B",
        "type": "object",
        "properties": {
            "b": {
                "title": "B",
                "anyOf": [
                    {
                        "title": "Foo",
                        "type": "object",
                        "properties": {"foo": {"title": "Foo", "type": "integer"}},
                        "required": ["foo"],
                    },
                    {
                        "title": "Bar",
                        "type": "object",
                        "properties": {"bar": {"title": "Bar", "type": "string"}},
                        "required": ["bar"],
                    },
                ],
            }
        },
        "required": ["b"],
    }
    assert replace_definitions(C.schema()) == {
        "title": "C",
        "type": "object",
        "properties": {
            "c": {
                "title": "C",
                "type": "array",
                "items": {
                    "title": "Foo",
                    "type": "object",
                    "properties": {"foo": {"title": "Foo", "type": "integer"}},
                    "required": ["foo"],
                },
            }
        },
        "required": ["c"],
    }
