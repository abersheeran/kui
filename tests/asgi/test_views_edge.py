import httpx
import pytest

from kui.asgi import HttpRoute, HttpView, Kui, required_method


def test_required_method_rejects_non_function():
    with pytest.raises(TypeError, match="can only decorate function"):

        @required_method("GET")
        class NotAFunction:
            pass


@pytest.mark.asyncio
async def test_required_method_options_returns_allow():
    app = Kui()

    async def handler():
        return "ok"

    app.router <<= HttpRoute("/explicit", handler) @ required_method("GET")

    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=app), base_url="http://testserver"
    ) as client:
        response = await client.options("/explicit")

    assert response.status_code == 200
    assert "GET" in response.headers["allow"]


@pytest.mark.asyncio
async def test_required_method_returns_405():
    app = Kui()

    async def handler():
        return "ok"

    app.router <<= HttpRoute("/only-get", handler) @ required_method("GET")

    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=app), base_url="http://testserver"
    ) as client:
        response = await client.post("/only-get")

    assert response.status_code == 405
    assert "GET" in response.headers["allow"]


@pytest.mark.asyncio
async def test_http_view_options_auto_generated():
    app = Kui()

    @app.router.http("/resource")
    class ResourceView(HttpView):
        @classmethod
        async def get(cls):
            return "ok"

        @classmethod
        async def post(cls):
            return "created", 201

    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=app), base_url="http://testserver"
    ) as client:
        response = await client.options("/resource")

    assert response.status_code == 200
    assert "GET" in response.headers["allow"]
    assert "POST" in response.headers["allow"]
    assert "OPTIONS" in response.headers["allow"]


@pytest.mark.asyncio
async def test_http_view_unsupported_method_405():
    app = Kui()

    @app.router.http("/resource")
    class ResourceView(HttpView):
        @classmethod
        async def get(cls):
            return "ok"

    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=app), base_url="http://testserver"
    ) as client:
        response = await client.delete("/resource")

    assert response.status_code == 405
    assert "GET" in response.headers["allow"]
