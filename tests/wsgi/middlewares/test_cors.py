from httpx import Client

from hintapi.middlewares import CORSMiddleware


def test_cors():
    cors_middleware = CORSMiddleware()

    from hintapi import HintAPI, HttpRoute

    app = HintAPI()

    def homepage():
        return "homepage"

    app.router << (HttpRoute("/", homepage) @ cors_middleware)

    with Client(
        app=app, base_url="http://localhost", headers={"origin": "testserver"}
    ) as client:
        resp = client.get("/")
        assert resp.headers["access-control-allow-origin"] == "testserver"
