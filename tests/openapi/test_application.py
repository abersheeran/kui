from http import HTTPStatus
from typing import List

import pytest
from async_asgi_testclient import TestClient
from pydantic import BaseModel

from indexpy import HttpRoute, HttpView, Index, Path, Routes, required_method
from indexpy.openapi import describe_extra_docs, describe_response
from indexpy.openapi.application import OpenAPI


@pytest.mark.asyncio
async def test_openapi_page():
    app = Index()
    openapi = OpenAPI("Title", "description", "1.0")
    app.router << "/docs" // openapi.routes

    @app.router.http("/hello")
    @describe_response(200, content=List[str])
    async def hello():
        """
        hello
        """
        pass

    class Username(BaseModel):
        name: str

    @app.router.http("/path/{name}")
    async def path(name: str = Path(...)):
        pass

    @app.router.http("/http-view")
    class HTTPClass(HttpView):
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

    middleware_routes = "/middleware" // Routes(
        HttpRoute("/path/{name}", path, "middleware-path"),
        HttpRoute("/http-view", HTTPClass, "middleware-HTTPClass"),
        http_middlewares=[just_middleware],
    )

    app.router << middleware_routes

    client = TestClient(app)
    response = await client.get("/docs", allow_redirects=False)
    assert response.status_code == 307
    assert response.headers["location"] == "http://localhost/docs/"

    response = await client.get("/docs/")
    assert response.status_code == 200

    response = await client.get("/docs/json")
    assert response.status_code == 200
    assert len(response.headers["hash"]) == 32

    openapi_docs_text = response.text
    assert (
        openapi_docs_text
        == '{"openapi":"3.0.0","info":{"title":"Title","description":"description","version":"1.0"},"paths":{"/http-view":{"get":{"summary":"...","description":"......","responses":{"200":{"description":"Request fulfilled, document follows","content":{"text/html":{"schema":{"type":"string"}}}}},"parameters":[{"name":"Authorization","in":"header","description":"JWT Token","required":true,"schema":{"type":"string"}}]},"post":{"summary":"...","description":"......","responses":{"201":{"description":"Document created, URL follows","content":{"application/json":{"schema":{"title":"Username","type":"object","properties":{"name":{"title":"Name","type":"string"}},"required":["name"]}}}}},"parameters":[{"name":"Authorization","in":"header","description":"JWT Token","required":true,"schema":{"type":"string"}}]},"delete":{"summary":"...","description":"......","responses":{"204":{"description":"Request fulfilled, nothing follows"}},"parameters":[{"name":"Authorization","in":"header","description":"JWT Token","required":true,"schema":{"type":"string"}}]}},"/middleware/http-view":{"get":{"summary":"...","description":"......","responses":{"200":{"description":"Request fulfilled, document follows","content":{"text/html":{"schema":{"type":"string"}}}}},"parameters":[{"name":"Authorization","in":"header","description":"JWT Token","required":true,"schema":{"type":"string"}}]},"post":{"summary":"...","description":"......","responses":{"201":{"description":"Document created, URL follows","content":{"application/json":{"schema":{"title":"Username","type":"object","properties":{"name":{"title":"Name","type":"string"}},"required":["name"]}}}}},"parameters":[{"name":"Authorization","in":"header","description":"JWT Token","required":true,"schema":{"type":"string"}}]},"delete":{"summary":"...","description":"......","responses":{"204":{"description":"Request fulfilled, nothing follows"}},"parameters":[{"name":"Authorization","in":"header","description":"JWT Token","required":true,"schema":{"type":"string"}}]}}},"tags":[],"servers":[{"url":"http://localhost","description":"Current server"}],"definitions":{}}'
    )


def test_openapi_single_function_summary_and_description():
    app = Index()
    openapi = OpenAPI("Title", "description", "1.0")
    app.router << "/docs" // openapi.routes

    @app.router.http.get("/0", name=None, summary="Summary", description="Description")
    async def _():
        return ""

    @app.router.http.get("/1", name=None, summary="Summary")
    async def _():
        return ""

    @app.router.http.get("/2", name=None, summary="Summary")
    async def _():
        """
        Description
        """
        return ""

    @app.router.http.get("/3", name=None)
    async def _():
        """
        Summary

        Description
        """
        return ""

    assert openapi._generate_path(app.router.search("http", "/0")[1], "/", {}) == {
        "get": {"summary": "Summary", "description": "Description"}
    }
    assert openapi._generate_path(app.router.search("http", "/1")[1], "/", {}) == {
        "get": {"summary": "Summary"}
    }
    assert openapi._generate_path(app.router.search("http", "/2")[1], "/", {}) == {
        "get": {"summary": "Summary", "description": "Description"}
    }
    assert openapi._generate_path(app.router.search("http", "/3")[1], "/", {}) == {
        "get": {"summary": "Summary", "description": "Description"}
    }


def test_openapi_single_function_tags():
    app = Index()
    openapi = OpenAPI("Title", "description", "1.0")
    app.router << "/docs" // openapi.routes

    @app.router.http.get("/", name=None, tags=["tag0"])
    async def homepage():
        return ""

    assert openapi._generate_path(app.router.search("http", "/")[1], "/", {}) == {
        "get": {"tags": ["tag0"]}
    }


def test_openapi_routes_tags():
    app = Index()
    openapi = OpenAPI("Title", "description", "1.0")
    app.router << "/docs" // openapi.routes

    async def homepage():
        return ""

    app.router << Routes(
        HttpRoute("/", homepage) @ required_method("GET"), tags=["tag0"]
    )

    assert openapi._generate_path(app.router.search("http", "/")[1], "/", {}) == {
        "get": {"tags": ["tag0"]}
    }
