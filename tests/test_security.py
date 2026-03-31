from typing import Tuple

import httpx
import pytest
from typing_extensions import Annotated

from kui.wsgi import (
    Depends,
    Kui,
    OpenAPI,
    api_key_auth_dependency,
    basic_auth,
    bearer_auth,
)


def test_basic_auth():
    app = Kui()

    @app.router.http("/")
    def homepage(user_and_password: Annotated[Tuple[str, str], Depends(basic_auth)]):
        return ", ".join(user_and_password)

    with httpx.Client(
        base_url="http://testServer",
        transport=httpx.WSGITransport(app=app),  # type: ignore
    ) as client:
        assert client.get("/").status_code == 401

        assert (
            client.get(
                "/", headers={"Authorization": "Basic dXNlcjpwYXNzd29yZA=="}
            ).text
            == "user, password"
        )


def test_api_key_auth():
    app = Kui()

    @app.router.http("/")
    def homepage(api_key: Annotated[str, Depends(api_key_auth_dependency("api-key"))]):
        return api_key

    with httpx.Client(
        base_url="http://testServer",
        transport=httpx.WSGITransport(app=app),  # type: ignore
    ) as client:
        assert client.get("/").status_code == 401

        assert client.get("/", headers={"api-key": "123"}).text == "123"


def test_bearer_auth():
    app = Kui()

    @app.router.http("/")
    def homepage(token: Annotated[str, Depends(bearer_auth)]):
        return token

    with httpx.Client(
        base_url="http://testServer",
        transport=httpx.WSGITransport(app=app),  # type: ignore
    ) as client:
        assert client.get("/").status_code == 401

        assert client.get("/", headers={"Authorization": "Bearer 123"}).text == "123"


def test_bearer_auth_missing_token():
    app = Kui()

    @app.router.http("/")
    def homepage(token: Annotated[str, Depends(bearer_auth)]):
        return token

    with httpx.Client(
        base_url="http://testServer",
        transport=httpx.WSGITransport(app=app),  # type: ignore
    ) as client:
        response = client.get("/", headers={"Authorization": "Bearer"})

    assert response.status_code == 401
    assert response.headers["WWW-Authenticate"] == "Bearer"


def test_bearer_auth_empty_header():
    app = Kui()

    @app.router.http("/")
    def homepage(token: Annotated[str, Depends(bearer_auth)]):
        return token

    with httpx.Client(
        base_url="http://testServer",
        transport=httpx.WSGITransport(app=app),  # type: ignore
    ) as client:
        response = client.get("/", headers={"Authorization": ""})

    assert response.status_code == 401
    assert response.headers["WWW-Authenticate"] == "Bearer"


def test_bearer_auth_wrong_scheme_returns_401():
    app = Kui()

    @app.router.http("/")
    def homepage(token: Annotated[str, Depends(bearer_auth)]):
        return token

    with httpx.Client(
        base_url="http://testServer",
        transport=httpx.WSGITransport(app=app),  # type: ignore
    ) as client:
        response = client.get("/", headers={"Authorization": "Basic token123"})

    assert response.status_code == 401
    assert response.headers["WWW-Authenticate"] == "Bearer"


def test_basic_auth_invalid_base64_returns_401():
    app = Kui()

    @app.router.http("/")
    def homepage(user_and_password: Annotated[Tuple[str, str], Depends(basic_auth)]):
        return ", ".join(user_and_password)

    with httpx.Client(
        base_url="http://testServer",
        transport=httpx.WSGITransport(app=app),  # type: ignore
    ) as client:
        response = client.get("/", headers={"Authorization": "Basic not-base64!"})

    assert response.status_code == 401
    assert response.headers["WWW-Authenticate"] == "Basic"


def test_basic_auth_without_separator_returns_401():
    app = Kui()

    @app.router.http("/")
    def homepage(user_and_password: Annotated[Tuple[str, str], Depends(basic_auth)]):
        return ", ".join(user_and_password)

    with httpx.Client(
        base_url="http://testServer",
        transport=httpx.WSGITransport(app=app),  # type: ignore
    ) as client:
        response = client.get("/", headers={"Authorization": "Basic bm9wYXNzd29yZA=="})

    assert response.status_code == 401
    assert response.headers["WWW-Authenticate"] == "Basic"


def test_basic_auth_wrong_scheme_returns_401():
    app = Kui()

    @app.router.http("/")
    def homepage(user_and_password: Annotated[Tuple[str, str], Depends(basic_auth)]):
        return ", ".join(user_and_password)

    with httpx.Client(
        base_url="http://testServer",
        transport=httpx.WSGITransport(app=app),  # type: ignore
    ) as client:
        response = client.get("/", headers={"Authorization": "Bearer abc"})

    assert response.status_code == 401
    assert response.headers["WWW-Authenticate"] == "Basic"


def test_api_key_auth_from_query():
    app = Kui()

    dependency = api_key_auth_dependency("api-key", "query")

    @app.router.http("/")
    def homepage(api_key: Annotated[str, Depends(dependency)]):
        return api_key

    with httpx.Client(
        base_url="http://testServer",
        transport=httpx.WSGITransport(app=app),  # type: ignore
    ) as client:
        response = client.get("/", params={"api-key": "query-value"})

    assert response.text == "query-value"


def test_api_key_auth_from_cookie():
    app = Kui()

    dependency = api_key_auth_dependency("api-key", "cookie")

    @app.router.http("/")
    def homepage(api_key: Annotated[str, Depends(dependency)]):
        return api_key

    with httpx.Client(
        base_url="http://testServer",
        transport=httpx.WSGITransport(app=app),  # type: ignore
        cookies={"api-key": "cookie-value"},
    ) as client:
        response = client.get("/")

    assert response.text == "cookie-value"


def test_api_key_auth_dependency_invalid_position_raises():
    with pytest.raises(
        ValueError,
        match=r"Invalid position invalid, must be one of \('query', 'header', 'cookie'\)",
    ):
        api_key_auth_dependency("api-key", "invalid")  # type: ignore[arg-type]


def test_auth_openapi():
    app = Kui()
    app.router <<= "/docs" // OpenAPI().routes

    def required_auth(token: Annotated[str, Depends(bearer_auth)]):
        return {"name": "username", "role": "User"}

    @app.router.http.get("/")
    def homepage(user: Annotated[dict, Depends(required_auth)]):
        return user

    with httpx.Client(
        base_url="http://testServer",
        transport=httpx.WSGITransport(app=app),  # type: ignore
    ) as client:
        assert client.get("/docs/json").json() == {
            "openapi": "3.1.0",
            "info": {"title": "Kuí API", "version": "1.0.0"},
            "paths": {
                "/": {"get": {"security": [{"BearerAuth": []}], "responses": {}}}
            },
            "tags": [],
            "components": {
                "securitySchemes": {"BearerAuth": {"type": "http", "scheme": "bearer"}},
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
