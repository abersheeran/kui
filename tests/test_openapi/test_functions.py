from index.openapi.functions import describe, partial
from index.openapi.models import Model, Field


def test_describe():
    class HTTP:
        @describe(200, "ok")
        @describe(400, "bad request")
        async def get(self):
            pass

    assert HTTP.get.__resps__[200]["model"] == "ok"
    assert HTTP.get.__resps__[400]["model"] == "bad request"


def test_partial():
    from starlette.datastructures import Headers

    class Header(Model):
        token: str

    header = Header(**Headers({"token": "123", "test": "12345g"}))
    assert header.token == "123"
    assert header.dict() == {"token": "123"}
