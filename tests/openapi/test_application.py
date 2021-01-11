import sys
from http import HTTPStatus
from typing import List

import pytest
from pydantic import BaseModel
from starlette.testclient import TestClient

from indexpy import Index
from indexpy.http import HTTPView, Path
from indexpy.openapi import describe_extra_docs, describe_response
from indexpy.openapi.application import OpenAPI
from indexpy.routing import HttpRoute, SubRoutes


@pytest.mark.skipif(
    sys.version_info < (3, 7),
    reason="The str behavior of typing.List has changed after 3.7",
)
def test_openapi_page():
    app = Index()
    openapi = OpenAPI("Title", "description", "1.0")
    app.router.extend(SubRoutes("/openapi", openapi.routes))

    @app.router.http("/hello", method="get")
    @describe_response(200, content=List[str])
    async def hello(request):
        """
        hello

        接口描述
        """
        pass

    class Username(BaseModel):
        name: str

    @app.router.http("/path/{name}", method="get")
    async def path(request, name: str = Path(...)):
        pass

    @app.router.http("/http-view")
    class HTTPClass(HTTPView):
        @describe_response(
            HTTPStatus.OK,
            content={
                "text/html": {
                    "schema": {"type": "string"},
                }
            },
        )
        async def get(self):
            """
            ...

            ......
            """

        @describe_response(HTTPStatus.CREATED, content=Username)
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
        describe_extra_docs(
            endpoint,
            {
                "parameters": [
                    {
                        "name": "Authorization",
                        "in": "header",
                        "description": "JWT Token",
                        "required": True,
                        "schema": {"type": "string"},
                    }
                ]
            },
        )
        return endpoint

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
    assert client.get("/openapi/docs").status_code == 200
    openapi_docs_text = client.get("/openapi/docs").text
    assert (
        openapi_docs_text
        == '{"openapi":"3.0.0","info":{"title":"Title","description":"description","version":"1.0"},"paths":{"/hello":{"get":{"summary":"hello","description":"接口描述","responses":{"200":{"description":"Request fulfilled, document follows","content":{"application/json":{"schema":{"title":"ParsingModel[List[str]]","type":"array","items":{"type":"string"}}}}}}}},"/http-view":{"get":{"summary":"...","description":"......","responses":{"200":{"description":"Request fulfilled, document follows","content":{"text/html":{"schema":{"type":"string"}}}}},"parameters":[{"name":"Authorization","in":"header","description":"JWT Token","required":true,"schema":{"type":"string"}}]},"post":{"summary":"...","description":"......","responses":{"201":{"description":"Document created, URL follows","content":{"application/json":{"schema":{"title":"Username","type":"object","properties":{"name":{"title":"Name","type":"string"}},"required":["name"]}}}}},"parameters":[{"name":"Authorization","in":"header","description":"JWT Token","required":true,"schema":{"type":"string"}}]},"delete":{"summary":"...","description":"......","responses":{"204":{"description":"Request fulfilled, nothing follows"}},"parameters":[{"name":"Authorization","in":"header","description":"JWT Token","required":true,"schema":{"type":"string"}}]}},"/path/{name}":{"get":{"parameters":[{"in":"path","name":"name","description":"","required":true,"schema":{"title":"Name","type":"string"}},{"name":"Authorization","in":"header","description":"JWT Token","required":true,"schema":{"type":"string"}}],"responses":{"422":{"content":{"application/json":{"schema":{"type":"array","items":{"type":"object","properties":{"loc":{"title":"Loc","description":"error field","type":"array","items":{"type":"string"}},"type":{"title":"Type","description":"error type","type":"string"},"msg":{"title":"Msg","description":"error message","type":"string"}},"required":["loc","type","msg"]}}}},"description":"Failed to verify request parameters"}}}},"/middleware/path/{name}":{"get":{"parameters":[{"in":"path","name":"name","description":"","required":true,"schema":{"title":"Name","type":"string"}},{"name":"Authorization","in":"header","description":"JWT Token","required":true,"schema":{"type":"string"}}],"responses":{"422":{"content":{"application/json":{"schema":{"type":"array","items":{"type":"object","properties":{"loc":{"title":"Loc","description":"error field","type":"array","items":{"type":"string"}},"type":{"title":"Type","description":"error type","type":"string"},"msg":{"title":"Msg","description":"error message","type":"string"}},"required":["loc","type","msg"]}}}},"description":"Failed to verify request parameters"}}}},"/middleware/http-view":{"get":{"summary":"...","description":"......","responses":{"200":{"description":"Request fulfilled, document follows","content":{"text/html":{"schema":{"type":"string"}}}}},"parameters":[{"name":"Authorization","in":"header","description":"JWT Token","required":true,"schema":{"type":"string"}}]},"post":{"summary":"...","description":"......","responses":{"201":{"description":"Document created, URL follows","content":{"application/json":{"schema":{"title":"Username","type":"object","properties":{"name":{"title":"Name","type":"string"}},"required":["name"]}}}}},"parameters":[{"name":"Authorization","in":"header","description":"JWT Token","required":true,"schema":{"type":"string"}}]},"delete":{"summary":"...","description":"......","responses":{"204":{"description":"Request fulfilled, nothing follows"}},"parameters":[{"name":"Authorization","in":"header","description":"JWT Token","required":true,"schema":{"type":"string"}}]}}},"tags":[],"servers":[{"url":"http://testserver","description":"Current server"}],"definitions":{}}'
    )
