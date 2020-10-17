from http import HTTPStatus

from pydantic import BaseModel
from starlette.testclient import TestClient

from indexpy import Index
from indexpy.http import HTTPView
from indexpy.openapi import describe_response
from indexpy.openapi.application import OpenAPI
from indexpy.routing import HttpRoute, SubRoutes


def test_openapi_page():
    app = Index()
    app.router.extend(
        SubRoutes("/openapi", OpenAPI("Title", "description", "1.0").routes)
    )

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
        @describe_response(
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

        @describe_response(HTTPStatus.CREATED, Path)
        async def post(self):
            """
            ...

            ......
            """

        @describe_response(HTTPStatus.NO_CONTENT)
        async def delete(self):
            """
            ...

            ......
            """

    def just_middleware(endpoint):
        async def w(c):
            return await endpoint(c)

        return w

    middleware_routes = SubRoutes(
        "/middleware",
        [
            HttpRoute("/path/{name}", path, "middleware-path", method="get"),
            HttpRoute("/http-view", HTTPClass, "middleware-HTTPClass"),
        ],
        http_middlewares=[just_middleware],
    )

    app.router.extend(middleware_routes)

    client = TestClient(app)
    assert client.get("/openapi/get").status_code == 200
    openapi_docs_text = client.get("/openapi/get").text
    assert "/http-view" in openapi_docs_text
    assert "/path/{name}" in openapi_docs_text
    assert "/middleware/path/{name}" in openapi_docs_text
    assert "/middleware/http-view" in openapi_docs_text
