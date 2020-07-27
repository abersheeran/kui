import pytest

from indexpy import Index
from indexpy.http import HTTPView
from starlette.testclient import TestClient


@pytest.fixture
def app():
    app = Index()

    @app.router.http("/cat", name=None)
    @app.router.http("/cat/{name}")
    class Cat(HTTPView):
        async def get(self, path=None):
            if path is None:
                return self.request.method
            return self.request.method + " " + path["name"]

        async def post(self, path=None):
            if path is None:
                return self.request.method
            return self.request.method + " " + path["name"]

    return app


def test_HTTPView(app):
    client = TestClient(app)
    assert client.get("/cat").text == "GET"
    assert client.get("/cat/aoliao").text == "GET aoliao"
    assert client.post("/cat").text == "POST"
    assert client.post("/cat/aoliao").text == "POST aoliao"
