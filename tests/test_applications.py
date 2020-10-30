from functools import wraps

import pytest
from pydantic import BaseModel
from starlette.testclient import TestClient

from indexpy.applications import Index, Dispatcher, MountApp
from indexpy.http.responses import HTMLResponse, convert
from indexpy.routing import HttpRoute, Routes, SubRoutes


@pytest.fixture
def app():
    app = Index()

    @app.router.http("/hello", method="get")
    async def hello(request):
        return "hello world"

    class Name(BaseModel):
        name: str

    class T:
        @app.router.http("/path/{name}", method="get")
        async def path(request, path: Name):
            return f"path {path.name}"

    def http_middleware(endpoint):
        @wraps(endpoint)
        async def wrapper(request):
            response = convert(await endpoint(request))
            response.body += b"; http middleware"
            return response

        return wrapper

    def only_empty(request):
        return b""

    def get_path(request, path: Name):
        return request.url.path

    def holiday(request):
        return "play game with girlfriend"

    app.router.extend(
        Routes(
            HttpRoute("/only/empty", only_empty, method="get"),
            SubRoutes(
                "/the-third-path",
                Routes(
                    HttpRoute("/path/{name}", get_path, method="get"),
                    Routes(
                        HttpRoute("/holiday", holiday, method="get"),
                        http_middlewares=[http_middleware],
                    ),
                ),
            ),
            http_middlewares=[http_middleware],
        )
    )

    return app


@pytest.mark.parametrize(
    "method,path,resp",
    [
        ("get", "/hello", "hello world"),
        ("get", "/path/index.py", "path index.py"),
        ("get", "/only/empty", "; http middleware"),
        (
            "get",
            "/the-third-path/path/name",
            "/the-third-path/path/name" + "; http middleware",
        ),
        (
            "get",
            "/the-third-path/holiday",
            "play game with girlfriend" + "; http middleware" + "; http middleware",
        ),
    ],
)
def test_app_router_success_response(app: Index, method: str, path: str, resp: str):
    assert getattr(TestClient(app), method)(path).text == resp


def test_dispather(app):
    async def echo_body(scope, receive, send):
        assert scope["type"] == "http"
        body = b""
        more_body = True
        while more_body:
            msg = await receive()
            body += msg.get("body", b"")
            more_body = msg.get("more_body", False)
        await send(
            {
                "type": "http.response.start",
                "status": 200,
                "headers": [
                    (b"content-type", b"text/plain"),
                    (b"Content-Length", str(len(body)).encode("latin1")),
                ],
            }
        )
        await send({"type": "http.response.body", "body": body})

    with TestClient(
        Dispatcher(
            app,
            MountApp("/echo", echo_body),
            MountApp("/sub", app),
        )
    ) as client:
        assert client.get("/hello").text == "hello world"
        assert client.get("/echo").text == "Not Found"
        assert client.get("/echo/").text == ""
        assert client.post("/echo/", data=b"echo").text == "echo"
        assert client.get("/sub/hello").text == "hello world"


def test_dispather_handle404(app):
    async def echo_body(scope, receive, send):
        assert scope["type"] == "http"
        body = b""
        more_body = True
        while more_body:
            msg = await receive()
            body += msg.get("body", b"")
            more_body = msg.get("more_body", False)
        if scope["path"] == "/":
            await send(
                {
                    "type": "http.response.start",
                    "status": 200,
                    "headers": [
                        (b"content-type", b"text/plain"),
                        (b"Content-Length", str(len(body)).encode("latin1")),
                    ],
                }
            )
            await send({"type": "http.response.body", "body": body})
        else:
            await send(
                {
                    "type": "http.response.start",
                    "status": 404,
                    "headers": [],
                }
            )
            await send({"type": "http.response.body", "body": b""})

    with TestClient(Dispatcher(app, MountApp("/echo", echo_body))) as client:
        assert client.get("/hello").text == "hello world"
        assert client.get("/echo").status_code == 404
        assert client.get("/echo/").status_code == 200
        assert client.post("/echo/c").status_code == 404
        assert client.post("/echo/c").text == ""

    with TestClient(
        Dispatcher(app, MountApp("/echo", echo_body), handle404=HTMLResponse("404"))
    ) as client:
        assert client.get("/hello").text == "hello world"
        assert client.get("/echo").status_code == 404
        assert client.get("/echo/").status_code == 200
        assert client.post("/echo/c").status_code == 200
        assert client.post("/echo/c").text == "404"
