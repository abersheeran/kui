import pytest
from pydantic import BaseModel
from starlette.testclient import TestClient

from indexpy import Index
from indexpy.http import Exclusive, HTTPView, Path


@pytest.fixture
def app():
    app = Index()

    @app.router.http("/", method="get")
    def homepage(request):
        return ""

    class Name(BaseModel):
        name: str = None

    @app.router.http("/cat", name=None)
    @app.router.http("/cat/{name}")
    class Cat(HTTPView):
        async def get(self, name: str = Path(None)):
            if not self.request.path_params:
                return self.request.method
            return self.request.method + " " + name

        async def post(self, path: Name = Exclusive("path", title="Cat Name")):
            if not self.request.path_params:
                return self.request.method
            return self.request.method + " " + path.name

    return app


def test_HTTPView(app):
    client = TestClient(app)
    assert client.get("/cat").text == "GET"
    assert client.get("/cat/aoliao").text == "GET aoliao"
    assert client.post("/cat").text == "POST"
    assert client.post("/cat/aoliao").text == "POST aoliao"


def test_function_view(app):
    client = TestClient(app)
    assert client.get("/").text == ""
    assert client.post("/").status_code == 405
