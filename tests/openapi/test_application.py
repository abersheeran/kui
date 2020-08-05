from http import HTTPStatus

from starlette.testclient import TestClient
from pydantic import BaseModel

from indexpy import Index
from indexpy.http import HTTPView
from indexpy.openapi import describe
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
        @describe(
            HTTPStatus.OK,
            """
            text/html:
                schema:
                    type: string
            """,
        )
        async def get(self):
            """
            ...

            ......
            """

        @describe(HTTPStatus.CREATED, Path)
        async def post(self):
            """
            ...

            ......
            """

        @describe(HTTPStatus.NO_CONTENT)
        async def delete(self):
            """
            ...

            ......
            """

    client = TestClient(app)
    assert client.get("/openapi/get").status_code == 200
