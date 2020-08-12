from functools import wraps

import pytest
from starlette.testclient import TestClient

from indexpy.applications import Index
from indexpy.routing import Routes, SubRoutes, HttpRoute
from indexpy.http.responses import convert


@pytest.fixture
def app():
    app = Index()

    @app.router.http("/hello", method="get")
    async def hello(request):
        return "hello world"

    @app.router.http("/path/{name}", method="get")
    async def path(request):
        return f"path {request.path_params['name']}"

    def http_middleware(endpoint):
        @wraps(endpoint)
        async def wrapper(request):
            response = convert(await endpoint(request))
            response.body += b"; http middleware"
            return response

        return wrapper

    def only_empty(request):
        return b""

    def get_path(request):
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
