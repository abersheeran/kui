from typing import Tuple

import httpx
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

    with httpx.Client(app=app, base_url="http://testServer") as client:
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

    with httpx.Client(app=app, base_url="http://testServer") as client:
        assert client.get("/").status_code == 401

        assert client.get("/", headers={"api-key": "123"}).text == "123"


def test_bearer_auth():
    app = Kui()

    @app.router.http("/")
    def homepage(token: Annotated[str, Depends(bearer_auth)]):
        return token

    with httpx.Client(app=app, base_url="http://testServer") as client:
        assert client.get("/").status_code == 401

        assert client.get("/", headers={"Authorization": "Bearer 123"}).text == "123"


def test_auth_openapi():
    app = Kui()
    app.router <<= "/docs" // OpenAPI().routes

    def required_auth(token: Annotated[str, Depends(bearer_auth)]):
        return {"name": "username", "role": "User"}

    @app.router.http.get("/")
    def homepage(user: Annotated[dict, Depends(required_auth)]):
        return user

    with httpx.Client(app=app, base_url="http://testServer") as client:
        assert client.get("/docs/json").json() == {
            "openapi": "3.0.3",
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
