import base64
from http import HTTPStatus
from typing import Callable, Tuple, Union

from typing_extensions import Annotated, Literal

from .exceptions import HTTPException
from .parameters.field_functions import (
    RequiredApiKeyAuth,
    RequiredBasicAuth,
    RequiredBearerAuth,
)

__all__ = [
    "bearer_auth",
]


def bearer_auth(
    authorization: Annotated[Union[str, None], RequiredBearerAuth()]
) -> Annotated[
    str,
    {
        401: {
            "description": HTTPStatus(401).description,
            "headers": {
                "WWW-Authenticate": {
                    "description": "Bearer token",
                    "schema": {"type": "string"},
                }
            },
        }
    },
]:
    """
    Bearer token authentication.
    """
    if authorization is None:
        raise HTTPException(
            401,
            headers={"WWW-Authenticate": "Bearer"},
        )
    try:
        type, token = authorization.strip().split(" ", maxsplit=1)
    except ValueError:
        raise HTTPException(
            401,
            headers={"WWW-Authenticate": "Bearer"},
        )
    if type != "Bearer":
        raise HTTPException(
            401,
            headers={"WWW-Authenticate": "Bearer"},
        )
    return token


def basic_auth(
    authorization: Annotated[Union[str, None], RequiredBasicAuth()]
) -> Annotated[
    Tuple[str, str],
    {
        401: {
            "description": HTTPStatus(401).description,
            "headers": {
                "WWW-Authenticate": {
                    "description": "Basic authentication",
                    "schema": {"type": "string"},
                }
            },
        }
    },
]:
    """
    Basic authentication.
    """
    if authorization is None:
        raise HTTPException(
            401,
            headers={"WWW-Authenticate": "Basic"},
        )
    try:
        type, token = authorization.strip().split(" ", maxsplit=1)
    except ValueError:
        raise HTTPException(
            401,
            headers={"WWW-Authenticate": "Basic"},
        )
    if type != "Basic":
        raise HTTPException(
            401,
            headers={"WWW-Authenticate": "Basic"},
        )
    username, password = base64.b64decode(token).decode("utf8").split(":")
    return username, password


def api_key_auth_dependency(
    name: str,
    position: Literal["query", "header", "cookie"] = "header",
) -> Callable[[Union[str, None]], str]:
    """
    Create API key authentication dependency.
    """

    def api_key_auth(
        api_key: Annotated[Union[str, None], RequiredApiKeyAuth(name, position)]
    ) -> Annotated[str, {401: {"description": HTTPStatus(401).description}}]:
        if api_key is None:
            raise HTTPException(401)
        return api_key

    return api_key_auth
