from __future__ import annotations

from httpx import Client

from kui.wsgi import allow_cors


def test_cors():
    cors_middleware = allow_cors()

    from kui.wsgi import HttpRoute, Kui

    app = Kui()

    def homepage():
        return "homepage"

    app.router <<= HttpRoute("/", homepage) @ cors_middleware

    with Client(
        app=app, base_url="http://testServer", headers={"origin": "testserver"}
    ) as client:
        resp = client.get("/")
        assert resp.headers["access-control-allow-origin"] == "testserver"
