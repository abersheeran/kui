import json
from typing import Callable

import pytest
from pydantic import BaseModel, Field, ValidationError

from kui.exceptions import (
    ExceptionMiddlewareBase,
    HTTPException,
    RequestValidationError,
)


class DummyExceptionMiddleware(ExceptionMiddlewareBase[Callable[[BaseException], str]]):
    def _init_internal_handlers(self) -> None:
        pass


class Payload(BaseModel):
    age: int


def make_validation_error() -> ValidationError:
    try:
        Payload(age="bad")  # type: ignore
    except ValidationError as exc:
        return exc
    raise AssertionError("Expected a ValidationError")


def test_lookup_handler_walks_exception_mro():
    class ParentError(Exception):
        pass

    class ChildError(ParentError):
        pass

    middleware = DummyExceptionMiddleware()
    handler = lambda exc: "parent"

    middleware.add_exception_handler(ParentError, handler)

    assert middleware.lookup_handler(ChildError()) is handler


def test_http_exception_status_handler_takes_precedence_over_exception_type_handler():
    middleware = DummyExceptionMiddleware()
    status_handler = lambda exc: "status"
    type_handler = lambda exc: "type"

    middleware.add_exception_handler(404, status_handler)
    middleware.add_exception_handler(HTTPException, type_handler)

    assert middleware.lookup_handler(HTTPException(status_code=404)) is status_handler


def test_http_exception_falls_back_to_exception_type_handler():
    middleware = DummyExceptionMiddleware()
    type_handler = lambda exc: "type"

    middleware.add_exception_handler(HTTPException, type_handler)

    assert middleware.lookup_handler(HTTPException(status_code=418)) is type_handler


def test_lookup_handler_returns_none_when_no_handler_is_registered():
    middleware = DummyExceptionMiddleware()

    assert middleware.lookup_handler(RuntimeError("boom")) is None


def test_request_validation_error_json_includes_in_field():
    request_validation_error = RequestValidationError(make_validation_error(), "query")

    errors = json.loads(request_validation_error.json())

    assert errors[0]["in"] == "query"


def test_request_validation_error_errors_include_in_field():
    request_validation_error = RequestValidationError(make_validation_error(), "body")

    errors = request_validation_error.errors()

    assert errors[0]["in"] == "body"


def test_request_validation_error_schema_matches_context_and_collection_indices():
    class ConstrainedPayload(BaseModel):
        count: int = Field(gt=0)
        values: list[int]

    with pytest.raises(ValidationError) as exc_info:
        ConstrainedPayload(count=0, values=["bad"])  # type: ignore

    error = RequestValidationError(exc_info.value, "body")
    errors = error.errors()
    assert isinstance(errors[0]["ctx"], dict)
    assert errors[0]["ctx"]
    assert errors[0]["loc"] == ("count",)
    assert errors[1]["loc"] == ("values", 0)
    assert all(item["in"] == "body" for item in errors)

    emitted = json.loads(error.json())
    assert emitted[0]["ctx"] == errors[0]["ctx"]
    assert emitted[0]["loc"] == ["count"]
    assert emitted[1]["loc"] == ["values", 0]
    assert all(item["in"] == "body" for item in emitted)

    assert error.schema()["items"]["required"] == ["loc", "type", "msg", "in"]
    properties = error.schema()["items"]["properties"]
    assert properties["loc"]["items"] == {
        "anyOf": [{"type": "string"}, {"type": "integer"}]
    }
    assert properties["ctx"] == {
        "title": "Context",
        "description": "error context",
        "type": "object",
        "additionalProperties": True,
    }
