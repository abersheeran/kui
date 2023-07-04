import json
from http import HTTPStatus
from typing import Any, List, Tuple

import httpx
import pytest
from async_asgi_testclient import TestClient
from pydantic import BaseModel
from typing_extensions import Annotated

from kui.asgi import (
    Depends,
    Header,
    HTMLResponse,
    HttpRoute,
    HttpView,
    JSONResponse,
    Kui,
    OpenAPI,
    Path,
    Routes,
    api_key_auth_dependency,
    basic_auth,
    bearer_auth,
    required_method,
)


@pytest.mark.asyncio
async def test_openapi_page():
    app = Kui()
    openapi = OpenAPI()
    app.router <<= Routes("/docs" // openapi.routes, namespace="docs")

    @app.router.http.get("/hello")
    async def hello() -> Annotated[Any, JSONResponse[200, {}, List[str]]]:
        """
        hello
        """
        pass

    class Username(BaseModel):
        name: str

    @app.router.http.get("/path/{name}")
    async def path(name: Annotated[str, Path(...)]):
        pass

    @app.router.http("/http-view")
    class HTTPClass(HttpView):
        @classmethod
        async def get(cls) -> Annotated[Any, HTMLResponse[200]]:
            """
            ...

            ......
            """

        @classmethod
        async def post(cls) -> Annotated[Any, JSONResponse[201, {}, Username]]:
            """
            ...

            ......
            """

        @classmethod
        async def delete(
            cls,
        ) -> Annotated[Any, {"204": {"description": HTTPStatus(204).description}}]:
            """
            ...

            ......
            """

    def just_middleware(endpoint):
        async def wrapper(
            authorization: Annotated[str, Header(..., description="JWT Token")]
        ) -> Annotated[Any, {"401": {"description": HTTPStatus(401).description}}]:
            return await endpoint()

        return wrapper

    middleware_routes = "/middleware" // Routes(
        HttpRoute("/path/{name}", path),
        HttpRoute("/http-view", HTTPClass),
        http_middlewares=[just_middleware],
        namespace="middleware",
    )

    app.router <<= middleware_routes

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
        "info": {"title": "Kuí API", "version": "1.0.0"},
        "paths": {
            "/hello": {
                "get": {
                    "summary": "hello",
                    "responses": {
                        "200": {
                            "description": "Request fulfilled, document follows",
                            "headers": {},
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
                            "headers": {},
                        }
                    },
                },
                "post": {
                    "summary": "...",
                    "description": "......",
                    "responses": {
                        "201": {
                            "description": "Document created, URL follows",
                            "headers": {},
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
                            "description": "",
                            "headers": {},
                            "content": {
                                "application/json": {
                                    "schema": {
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
                                                    "enum": [
                                                        "path",
                                                        "query",
                                                        "header",
                                                        "cookie",
                                                        "body",
                                                    ],
                                                },
                                            },
                                            "required": ["loc", "type", "msg"],
                                        },
                                    }
                                }
                            },
                        }
                    },
                }
            },
            "/middleware/http-view": {
                "get": {
                    "summary": "...",
                    "description": "......",
                    "parameters": [
                        {
                            "in": "header",
                            "name": "authorization",
                            "description": "JWT Token",
                            "required": True,
                            "schema": {"title": "Authorization", "type": "string"},
                            "deprecated": False,
                        }
                    ],
                    "responses": {
                        "200": {
                            "description": "Request fulfilled, document follows",
                            "content": {"text/html": {"schema": {"type": "string"}}},
                            "headers": {},
                        },
                        "401": {
                            "description": "No permission -- see authorization schemes"
                        },
                        "422": {
                            "description": "",
                            "headers": {},
                            "content": {
                                "application/json": {
                                    "schema": {
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
                                                    "enum": [
                                                        "path",
                                                        "query",
                                                        "header",
                                                        "cookie",
                                                        "body",
                                                    ],
                                                },
                                            },
                                            "required": ["loc", "type", "msg"],
                                        },
                                    }
                                }
                            },
                        },
                    },
                },
                "post": {
                    "summary": "...",
                    "description": "......",
                    "parameters": [
                        {
                            "in": "header",
                            "name": "authorization",
                            "description": "JWT Token",
                            "required": True,
                            "schema": {"title": "Authorization", "type": "string"},
                            "deprecated": False,
                        }
                    ],
                    "responses": {
                        "201": {
                            "description": "Document created, URL follows",
                            "headers": {},
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
                        },
                        "401": {
                            "description": "No permission -- see authorization schemes"
                        },
                        "422": {
                            "description": "",
                            "headers": {},
                            "content": {
                                "application/json": {
                                    "schema": {
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
                                                    "enum": [
                                                        "path",
                                                        "query",
                                                        "header",
                                                        "cookie",
                                                        "body",
                                                    ],
                                                },
                                            },
                                            "required": ["loc", "type", "msg"],
                                        },
                                    }
                                }
                            },
                        },
                    },
                },
                "delete": {
                    "summary": "...",
                    "description": "......",
                    "parameters": [
                        {
                            "in": "header",
                            "name": "authorization",
                            "description": "JWT Token",
                            "required": True,
                            "schema": {"title": "Authorization", "type": "string"},
                            "deprecated": False,
                        }
                    ],
                    "responses": {
                        "204": {"description": "Request fulfilled, nothing follows"},
                        "401": {
                            "description": "No permission -- see authorization schemes"
                        },
                        "422": {
                            "description": "",
                            "headers": {},
                            "content": {
                                "application/json": {
                                    "schema": {
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
                                                    "enum": [
                                                        "path",
                                                        "query",
                                                        "header",
                                                        "cookie",
                                                        "body",
                                                    ],
                                                },
                                            },
                                            "required": ["loc", "type", "msg"],
                                        },
                                    }
                                }
                            },
                        },
                    },
                },
            },
        },
        "tags": [],
        "components": {"schemas": {}},
        "servers": [
            {"url": "/", "description": "Current server"},
            {
                "url": "{scheme}://{address}/",
                "description": "Custom API Server Host",
                "variables": {
                    "scheme": {
                        "default": "http",
                        "enum": ["http", "https"],
                        "description": "http or https",
                    },
                    "address": {
                        "default": "localhost",
                        "description": "api server's host[:port]",
                    },
                },
            },
        ],
    }, str(json.loads(openapi_docs_text))


def test_openapi_single_function_summary_and_description():
    app = Kui()
    openapi = OpenAPI()
    app.router <<= "/docs" // openapi.routes

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

    assert openapi._generate_path(app, app.router.search("http", "/0")[1], "/") == {
        "get": {"summary": "Summary", "description": "Description"}
    }
    assert openapi._generate_path(app, app.router.search("http", "/1")[1], "/") == {
        "get": {"summary": "Summary"}
    }
    assert openapi._generate_path(app, app.router.search("http", "/2")[1], "/") == {
        "get": {"summary": "Summary"}
    }
    assert openapi._generate_path(app, app.router.search("http", "/3")[1], "/") == {
        "get": {"summary": "Summary", "description": "Description"}
    }


def test_openapi_single_function_tags():
    app = Kui()
    openapi = OpenAPI()
    app.router <<= "/docs" // openapi.routes

    @app.router.http.get("/", name=None, tags=["tag0"])
    async def homepage():
        return ""

    assert openapi._generate_path(app, app.router.search("http", "/")[1], "/") == (
        {"get": {"tags": ["tag0"]}}
    )


def test_openapi_routes_tags():
    app = Kui()
    openapi = OpenAPI()
    app.router <<= "/docs" // openapi.routes

    async def homepage():
        return ""

    app.router <<= Routes(
        HttpRoute("/", homepage) @ required_method("GET"), tags=["tag0"]
    )

    assert openapi._generate_path(app, app.router.search("http", "/")[1], "/") == (
        {"get": {"tags": ["tag0"]}}
    )


@pytest.mark.asyncio
async def test_openapi_security():
    app = Kui()
    openapi = OpenAPI()
    app.router <<= "/docs" // openapi.routes

    @app.router.http.get("/basic")
    async def basic(user_and_password: Annotated[Tuple[str, str], Depends(basic_auth)]):
        return ", ".join(user_and_password)

    @app.router.http.get("/bearer")
    async def bearer(token: Annotated[str, Depends(bearer_auth)]):
        return token

    @app.router.http.get("/api-key")
    async def api_key(
        api_key: Annotated[str, Depends(api_key_auth_dependency("api-key"))]
    ):
        return api_key

    async with httpx.AsyncClient(app=app, base_url="http://testserver") as client:
        resp = await client.get("/docs/json")
        openapi_json = resp.json()

        assert openapi_json == {
            "openapi": "3.0.3",
            "info": {"title": "Kuí API", "version": "1.0.0"},
            "paths": {
                "/basic": {
                    "get": {
                        "security": [{"BasicAuth": []}],
                        "responses": {
                            "401": {
                                "description": "No permission -- see authorization schemes",
                                "headers": {
                                    "WWW-Authenticate": {
                                        "description": "Basic authentication",
                                        "schema": {"type": "string"},
                                    }
                                },
                            }
                        },
                    }
                },
                "/bearer": {
                    "get": {
                        "security": [{"BearerAuth": []}],
                        "responses": {
                            "401": {
                                "description": "No permission -- see authorization schemes",
                                "headers": {
                                    "WWW-Authenticate": {
                                        "description": "Bearer token",
                                        "schema": {"type": "string"},
                                    }
                                },
                            }
                        },
                    }
                },
                "/api-key": {
                    "get": {
                        "security": [{"ApiKeyAuth": []}],
                        "responses": {
                            "401": {
                                "description": "No permission -- see authorization schemes"
                            }
                        },
                    }
                },
            },
            "tags": [],
            "components": {
                "securitySchemes": {
                    "BasicAuth": {"type": "http", "scheme": "basic"},
                    "BearerAuth": {"type": "http", "scheme": "bearer"},
                    "ApiKeyAuth": {"type": "apiKey", "name": "api-key", "in": "header"},
                },
                "schemas": {},
            },
            "servers": [
                {"url": "/", "description": "Current server"},
                {
                    "url": "{scheme}://{address}/",
                    "description": "Custom API Server Host",
                    "variables": {
                        "scheme": {
                            "default": "http",
                            "enum": ["http", "https"],
                            "description": "http or https",
                        },
                        "address": {
                            "default": "testserver",
                            "description": "api server's host[:port]",
                        },
                    },
                },
            ],
        }


def test_openapi_depend_response():
    app = Kui()
    openapi = OpenAPI()
    app.router <<= "/docs" // openapi.routes

    async def get_current_user(
        authorization: Annotated[str, Header(..., description="JWT Token")]
    ) -> Annotated[Any, {"401": {"description": HTTPStatus(401).description}}]:
        pass

    @app.router.http.get("/")
    async def homepage(user: Annotated[Any, Depends(get_current_user)]) -> Any:
        pass

    assert openapi._generate_path(app, app.router.search("http", "/")[1], "/") == (
        {
            "get": {
                "parameters": [
                    {
                        "in": "header",
                        "name": "authorization",
                        "description": "JWT Token",
                        "required": True,
                        "schema": {"title": "Authorization", "type": "string"},
                        "deprecated": False,
                    }
                ],
                "responses": {
                    "422": {
                        "description": "",
                        "headers": {},
                        "content": {
                            "application/json": {
                                "schema": {
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
                                                "enum": [
                                                    "path",
                                                    "query",
                                                    "header",
                                                    "cookie",
                                                    "body",
                                                ],
                                            },
                                        },
                                        "required": ["loc", "type", "msg"],
                                    },
                                }
                            }
                        },
                    },
                    "401": {
                        "description": "No permission -- see authorization schemes",
                    },
                },
            }
        }
    )


def test_openapi_multi_type_responses():
    app = Kui()
    openapi = OpenAPI()
    app.router <<= "/docs" // openapi.routes

    class Message(BaseModel):
        message: str

    @app.router.http.get("/")
    async def homepage() -> Annotated[
        Any, JSONResponse[200, {}, Message], HTMLResponse[200]
    ]:
        pass

    assert openapi._generate_path(app, app.router.search("http", "/")[1], "/") == {
        "get": {
            "responses": {
                "200": {
                    "description": "Request fulfilled, document follows",
                    "headers": {},
                    "content": {
                        "application/json": {
                            "schema": {
                                "type": "object",
                                "properties": {
                                    "message": {"title": "Message", "type": "string"}
                                },
                                "required": ["message"],
                            }
                        },
                        "text/html": {"schema": {"type": "string"}},
                    },
                }
            }
        }
    }


@pytest.mark.asyncio
async def test_openapi_components_schemas():
    app = Kui()
    openapi = OpenAPI()
    app.router <<= Routes("/docs" // openapi.routes, namespace="docs")

    class M(BaseModel):
        message: str

    class N(BaseModel):
        m: M

    @app.router.http.get("/hello")
    async def hello() -> Annotated[Any, JSONResponse[200, {}, N]]:
        """
        hello
        """
        pass

    client = TestClient(app)
    response = await client.get("/docs/json")
    assert response.status_code == 200
    assert len(response.headers["hash"]) == 32

    openapi_docs_text = response.text
    assert json.loads(openapi_docs_text) == {
        "openapi": "3.0.3",
        "info": {"title": "Kuí API", "version": "1.0.0"},
        "paths": {
            "/hello": {
                "get": {
                    "summary": "hello",
                    "responses": {
                        "200": {
                            "description": "Request fulfilled, document follows",
                            "headers": {},
                            "content": {
                                "application/json": {
                                    "schema": {
                                        "properties": {
                                            "m": {"$ref": "#/components/schemas/M"}
                                        },
                                        "required": ["m"],
                                        "type": "object",
                                    }
                                }
                            },
                        }
                    },
                }
            }
        },
        "tags": [],
        "components": {
            "schemas": {
                "M": {
                    "properties": {"message": {"title": "Message", "type": "string"}},
                    "required": ["message"],
                    "title": "M",
                    "type": "object",
                }
            }
        },
        "servers": [
            {"url": "/", "description": "Current server"},
            {
                "url": "{scheme}://{address}/",
                "description": "Custom API Server Host",
                "variables": {
                    "scheme": {
                        "default": "http",
                        "enum": ["http", "https"],
                        "description": "http or https",
                    },
                    "address": {
                        "default": "localhost",
                        "description": "api server's host[:port]",
                    },
                },
            },
        ],
    }, openapi_docs_text
