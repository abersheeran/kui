import pytest

from indexpy.openapi.functions import (
    describe_response,
    describe_responses,
    merge_openapi_info,
)


def test_describe_response():
    class HTTP:
        @describe_response(200, "ok")
        @describe_response(400, "bad request")
        async def get(self):
            pass

    assert HTTP.get.__responses__ == {
        200: {"description": "ok"},
        400: {"description": "bad request"},
    }


def test_describe_responses():
    class HTTP:
        @describe_responses(
            {
                200: {"description": "ok"},
                400: {"description": "bad request"},
            }
        )
        async def get(self):
            pass

    assert HTTP.get.__responses__ == {
        200: {"description": "ok"},
        400: {"description": "bad request"},
    }


@pytest.mark.parametrize(
    "f,s,r",
    [
        ({"a": 1}, {"b": 1}, {"a": 1, "b": 1}),
        ({"a": {"a": 1}, "b": 1}, {"a": {"b": 1}}, {"a": {"a": 1, "b": 1}, "b": 1}),
        ({"a": (1, 2)}, {"a": (3,)}, {"a": [1, 2, 3]}),
    ],
)
def test_merge_openapi_info(f, s, r):
    assert merge_openapi_info(f, s) == r
