import base64
from http import HTTPStatus
from typing import Callable, Tuple, Type, Union

from pydantic import Field
from typing_extensions import Annotated, Literal

from .exceptions import HTTPException
from .parameters.fields import InCookie, InHeader, InQuery

__all__ = [
    "bearer_auth",
]


def bearer_auth(
    authorization: Annotated[
        Union[str, None],
        Field(default=None, alias="authorization", title="Bearer Auth"),
        InHeader(
            security={
                "scheme": {"BearerAuth": {"type": "http", "scheme": "bearer"}},
                "required": {"BearerAuth": []},
            }
        ),
    ],
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
    authorization: Annotated[
        Union[str, None],
        Field(default=None, alias="authorization", title="Basic Auth"),
        InHeader(
            security={
                "scheme": {"BasicAuth": {"type": "http", "scheme": "basic"}},
                "required": {"BasicAuth": []},
            }
        ),
    ],
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
    class_: Union[Type[InQuery], Type[InHeader], Type[InCookie]]
    if position == "query":
        class_ = InQuery
    elif position == "header":
        class_ = InHeader
    elif position == "cookie":
        class_ = InCookie
    else:
        raise ValueError(
            f"Invalid position {position}, must be one of ('query', 'header', 'cookie')"
        )

    def api_key_auth(
        api_key: Annotated[
            Union[str, None],
            Field(
                default=None,
                alias=name,
                title="API Key",
            ),
            class_(
                security={
                    "scheme": {
                        "ApiKeyAuth": {"type": "apiKey", "name": name, "in": position}
                    },
                    "required": {"ApiKeyAuth": []},
                }
            ),
        ],
    ) -> Annotated[str, {401: {"description": HTTPStatus(401).description}}]:
        if api_key is None:
            raise HTTPException(401)
        return api_key

    return api_key_auth
