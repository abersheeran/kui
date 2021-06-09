import pytest
from async_asgi_testclient import TestClient

from indexpy.middlewares import CORSMiddleware


@pytest.mark.asyncio
async def test_cors():
    cors_middleware = CORSMiddleware()

    from indexpy import Index, HttpRoute

    app = Index()

    async def homepage():
        return "homepage"

    app.router << (HttpRoute("/", homepage) @ cors_middleware)

    async with TestClient(app, headers={"origin": "testserver"}) as client:
        resp = await client.get("/")
        assert resp.headers["access-control-allow-origin"] == "testserver"
