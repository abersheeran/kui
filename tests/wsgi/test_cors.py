from __future__ import annotations

import re

import httpx

from kui.wsgi import allow_cors


def test_cors():
    cors_middleware = allow_cors()

    from kui.wsgi import HttpRoute, Kui

    app = Kui()

    def homepage():
        return "homepage"

    app.router <<= HttpRoute("/", homepage) @ cors_middleware

    with httpx.Client(
        base_url="http://testServer",
        headers={"origin": "testserver"},
        transport=httpx.WSGITransport(app=app),  # type: ignore
    ) as client:
        resp = client.get("/")
        assert resp.headers["access-control-allow-origin"] == "testserver"

        resp = client.options("/")
        assert resp.headers["access-control-allow-origin"] == "testserver"


def test_cors_global():
    from kui.wsgi import HttpRoute, Kui

    app = Kui(
        cors_config={
            "allow_origins": [
                re.compile("testserver"),
            ]
        }
    )

    def homepage():
        return "homepage"

    app.router <<= HttpRoute("/", homepage)

    with httpx.Client(
        base_url="http://testServer",
        transport=httpx.WSGITransport(app=app),  # type: ignore
        headers={"origin": "testserver"},
    ) as client:
        resp = client.get("/")
        assert resp.headers["access-control-allow-origin"] == "testserver"

        resp = client.options("/")
        assert resp.headers["access-control-allow-origin"] == "testserver"
