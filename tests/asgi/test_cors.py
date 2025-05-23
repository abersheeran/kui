from __future__ import annotations

import re

import httpx
import pytest

from kui.asgi import allow_cors


@pytest.mark.asyncio
async def test_cors():
    cors_middleware = allow_cors()

    from kui.asgi import HttpRoute, Kui

    app = Kui()

    async def homepage():
        return "homepage"

    app.router <<= HttpRoute("/", homepage) @ cors_middleware

    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=app),
        base_url="http://testserver",
        headers={"origin": "testserver"},
    ) as client:
        resp = await client.get("/")
        assert resp.headers["access-control-allow-origin"] == "testserver"

        resp = await client.options("/")
        assert resp.headers["access-control-allow-origin"] == "testserver"


@pytest.mark.asyncio
async def test_cors_global():
    from kui.asgi import HttpRoute, Kui

    app = Kui(
        cors_config={
            "allow_origins": [
                re.compile("testserver"),
            ]
        }
    )

    async def homepage():
        return "homepage"

    app.router <<= HttpRoute("/", homepage)

    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=app),
        base_url="http://testserver",
        headers={"origin": "testserver"},
    ) as client:
        resp = await client.get("/")
        assert resp.headers["access-control-allow-origin"] == "testserver"

        resp = await client.options("/")
        assert resp.headers["access-control-allow-origin"] == "testserver"
