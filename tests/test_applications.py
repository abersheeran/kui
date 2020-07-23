import pytest

from indexpy.applications import Index
from starlette.testclient import TestClient


@pytest.fixture
def app():
    app = Index()

    @app.router.http("/hello", method="get")
    async def hello(request):
        return "hello world"

    @app.router.http("/path/{name}", method="get")
    async def path(request, path):
        return f"path {path['name']}"

    return app


@pytest.mark.parametrize(
    "method,path,resp",
    [("get", "/hello", "hello world"), ("get", "/path/index.py", "path index.py")],
)
def test_app_router_success_response(app: Index, method: str, path: str, resp: str):
    assert getattr(TestClient(app), method)(path).text == resp
