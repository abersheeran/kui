import json
from http import HTTPStatus
from typing import List

import pytest
from async_asgi_testclient import TestClient
from pydantic import BaseModel

from indexpy import HttpRoute, HttpView, Index, Path, Routes, required_method
from indexpy.field_functions import Header
from indexpy.openapi import describe_response
from indexpy.openapi.application import OpenAPI


@pytest.mark.asyncio
async def test_openapi_page():
    app = Index()
    openapi = OpenAPI()
    app.router << Routes("/docs" // openapi.routes, namespace="docs")
    assert app.router.url_for("docs:json_docs") == "/docs/json"

    @app.router.http.get("/hello")
    @describe_response(200, content=List[str])
    async def hello():
        """
        hello
        """
        pass

    class Username(BaseModel):
        name: str

    @app.router.http.get("/path/{name}")
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
        async def wrapper(authorization: str = Header(..., description="JWT Token")):
            return await endpoint()

        return wrapper

    middleware_routes = "/middleware" // Routes(
        HttpRoute("/path/{name}", path),
        HttpRoute("/http-view", HTTPClass),
        http_middlewares=[just_middleware],
        namespace="middleware",
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
    assert json.loads(openapi_docs_text) == {
        "openapi": "3.0.3",
        "info": {"title": "IndexPy API", "version": "1.0.0"},
        "paths": {
            "/hello": {
                "get": {
                    "summary": "hello",
                    "responses": {
                        "200": {
                            "description": "Request fulfilled, document follows",
                            "content": {
                                "application/json": {
                                    "schema": {
                                        "type": "array",
                                        "items": {"type": "string"},
                                    }
                                }
                            },
                        }
                    },
                }
            },
            "/http-view": {
                "get": {
                    "summary": "...",
                    "description": "......",
                    "responses": {
                        "200": {
                            "description": "Request fulfilled, document follows",
                            "content": {"text/html": {"schema": {"type": "string"}}},
                        }
                    },
                },
                "post": {
                    "summary": "...",
                    "description": "......",
                    "responses": {
                        "201": {
                            "description": "Document created, URL follows",
                            "content": {
                                "application/json": {
                                    "schema": {
                                        "type": "object",
                                        "properties": {
                                            "name": {"title": "Name", "type": "string"}
                                        },
                                        "required": ["name"],
                                    }
                                }
                            },
                        }
                    },
                },
                "delete": {
                    "summary": "...",
                    "description": "......",
                    "responses": {
                        "204": {"description": "Request fulfilled, nothing follows"}
                    },
                },
            },
            "/path/{name}": {
                "get": {
                    "parameters": [
                        {
                            "in": "path",
                            "name": "name",
                            "description": "",
                            "required": True,
                            "schema": {"title": "Name", "type": "string"},
                            "deprecated": False,
                        }
                    ],
                    "responses": {
                        "422": {
                            "content": {
                                "application/json": {
                                    "schema": {
                                        "$ref": "#/components/schemas/RequestValidationError"
                                    }
                                }
                            },
                            "description": "Failed to verify request parameters",
                        }
                    },
                }
            },
            "/middleware/http-view": {
                "get": {
                    "summary": "...",
                    "description": "......",
                    "responses": {
                        "200": {
                            "description": "Request fulfilled, document follows",
                            "content": {"text/html": {"schema": {"type": "string"}}},
                        }
                    },
                },
                "post": {
                    "summary": "...",
                    "description": "......",
                    "responses": {
                        "201": {
                            "description": "Document created, URL follows",
                            "content": {
                                "application/json": {
                                    "schema": {
                                        "type": "object",
                                        "properties": {
                                            "name": {"title": "Name", "type": "string"}
                                        },
                                        "required": ["name"],
                                    }
                                }
                            },
                        }
                    },
                },
                "delete": {
                    "summary": "...",
                    "description": "......",
                    "responses": {
                        "204": {"description": "Request fulfilled, nothing follows"}
                    },
                },
            },
        },
        "tags": [],
        "components": {
            "securitySchemes": {},
            "schemas": {
                "RequestValidationError": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "loc": {
                                "title": "Location",
                                "description": "error field",
                                "type": "array",
                                "items": {"type": "string"},
                            },
                            "type": {
                                "title": "Type",
                                "description": "error type",
                                "type": "string",
                            },
                            "msg": {
                                "title": "Message",
                                "description": "error message",
                                "type": "string",
                            },
                            "ctx": {
                                "title": "Context",
                                "description": "error context",
                                "type": "string",
                            },
                            "in": {
                                "title": "In",
                                "type": "string",
                                "enum": ["path", "query", "header", "cookie", "body"],
                            },
                        },
                        "required": ["loc", "type", "msg"],
                    },
                }
            },
        },
        "servers": [{"url": "http://localhost", "description": "Current server"}],
    }, str(json.loads(openapi_docs_text))


def test_openapi_single_function_summary_and_description():
    app = Index()
    openapi = OpenAPI()
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

    assert openapi._generate_path(app.router.search("http", "/0")[1], "/")[0] == {
        "get": {"summary": "Summary", "description": "Description"}
    }
    assert openapi._generate_path(app.router.search("http", "/1")[1], "/")[0] == {
        "get": {"summary": "Summary"}
    }
    assert openapi._generate_path(app.router.search("http", "/2")[1], "/")[0] == {
        "get": {"summary": "Summary", "description": "Description"}
    }
    assert openapi._generate_path(app.router.search("http", "/3")[1], "/")[0] == {
        "get": {"summary": "Summary", "description": "Description"}
    }


def test_openapi_single_function_tags():
    app = Index()
    openapi = OpenAPI()
    app.router << "/docs" // openapi.routes

    @app.router.http.get("/", name=None, tags=["tag0"])
    async def homepage():
        return ""

    assert openapi._generate_path(app.router.search("http", "/")[1], "/") == (
        {"get": {"tags": ["tag0"]}},
        {},
    )


def test_openapi_routes_tags():
    app = Index()
    openapi = OpenAPI()
    app.router << "/docs" // openapi.routes

    async def homepage():
        return ""

    app.router << Routes(
        HttpRoute("/", homepage) @ required_method("GET"), tags=["tag0"]
    )

    assert openapi._generate_path(app.router.search("http", "/")[1], "/") == (
        {"get": {"tags": ["tag0"]}},
        {},
    )
