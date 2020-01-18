from typing import Union, List

from index.openapi.schema import replace_definitions
from index.openapi import models


def test_schema_models():
    class Foo(models.Model):
        foo: int

    class Bar(models.Model):
        bar: str

    class A(models.Model):
        a: Foo

    class B(models.Model):
        b: Union[Foo, Bar]

    class C(models.Model):
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
