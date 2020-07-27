from starlette.testclient import TestClient
from pydantic import BaseModel

from indexpy import Index
from indexpy.http import HTTPView
from indexpy.openapi.application import OpenAPI


def test_openapi_page():
    app = Index(mount_apps=[("/openapi", OpenAPI("Title", "description", "1.0"))])

    @app.router.http("/hello", method="get")
    async def hello(request):
        """
        hello

        hello description
        """
        pass

    class Path(BaseModel):
        name: str

    @app.router.http("/path/{name}", method="get")
    async def path(request, path: Path):
        pass

    @app.router.http("/http-view")
    class HTTPClass(HTTPView):
        async def get(self):
            """
            ...

            ......
            """

        async def post(self):
            """
            ...

            ......
            """

        async def delete(self):
            """
            ...

            ......
            """

    client = TestClient(app)
    assert client.get("/openapi/get").status_code == 200
