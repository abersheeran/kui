from typing import Tuple

import httpx
from typing_extensions import Annotated

from kui.wsgi import Depends, Kui, api_key_auth_dependency, basic_auth, bearer_auth


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
