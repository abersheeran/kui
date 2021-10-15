from __future__ import annotations

import typing
from http import HTTPStatus

from baize.asgi import FileResponse, HTMLResponse
from baize.asgi import JSONResponse as _JSONResponse
from baize.asgi import PlainTextResponse, RedirectResponse
from baize.asgi import Response as HttpResponse
from baize.asgi import SendEventResponse, ServerSentEvent, StreamResponse
from pydantic import BaseModel, create_model
from pydantic.json import pydantic_encoder
from pydantic.typing import display_as_type

from .requests import request
from .utils import safe_issubclass

__all__ = [
    "convert_response",
    "HttpResponse",
    "FileResponse",
    "HTMLResponse",
    "JSONResponse",
    "PlainTextResponse",
    "RedirectResponse",
    "SendEventResponse",
    "ServerSentEvent",
    "StreamResponse",
    "TemplateResponse",
]


class JSONResponse(_JSONResponse):
    def __init__(
        self,
        content: typing.Any,
        status_code: int = 200,
        headers: typing.Mapping[str, str] = None,
        **kwargs: typing.Any,
    ) -> None:
        json_kwargs: typing.Dict[str, typing.Any] = {
            "default": pydantic_encoder,
        }
        json_kwargs.update(**kwargs)
        super().__init__(
            content, status_code=status_code, headers=headers, **json_kwargs
        )


def TemplateResponse(
    name: str,
    context: typing.Mapping[str, typing.Any],
    status_code: int = 200,
    headers: typing.Mapping[str, str] = None,
    media_type: str = None,
    charset: str = None,
) -> HttpResponse:
    templates = request.app.templates
    if templates is None:
        raise RuntimeError(
            "You must assign a value to `app.templates` to use TemplateResponse"
        )

    return templates.TemplateResponse(
        name, context, status_code, headers, media_type, charset
    )


def convert_response(response: typing.Any) -> HttpResponse:
    """
    shortcut for automatic

    Example:

        response = convert(response)

    It is equivalent to:

        if isinstance(response, tuple):
            response = automatic(*response)
        else:
            response = automatic(response)

    """
    if isinstance(response, tuple):
        return request.app.response_converter(*response)
    else:
        return request.app.response_converter(response)


def html_response__class_getitem__(parameters):
    """
    Use HTMLResponse[status, headers] to describe response
    """
    if isinstance(parameters, tuple):
        status_code, headers = parameters
    else:
        status_code, headers = parameters, {}
    assert isinstance(status_code, int)
    docs = {
        str(status_code): {
            "description": HTTPStatus(status_code).description,
            "content": {"text/html": {"schema": {"type": "string"}}},
        }
    }
    if headers:
        docs[str(status_code)]["headers"] = headers
    return docs


HTMLResponse.__class_getitem__ = html_response__class_getitem__  # type: ignore


def plain_text_response__class_getitem__(parameters):
    """
    Use PlainTextResponse[status, headers] to describe response
    """
    if isinstance(parameters, tuple):
        status_code, headers = parameters
    else:
        status_code, headers = parameters, {}
    assert isinstance(status_code, int)
    docs = {
        str(status_code): {
            "description": HTTPStatus(status_code).description,
            "content": {"text/plain": {"schema": {"type": "string"}}},
        }
    }
    if headers:
        docs[str(status_code)]["headers"] = headers
    return docs


PlainTextResponse.__class_getitem__ = plain_text_response__class_getitem__  # type: ignore


def redirect_response__class_getitem__(parameters):
    """
    Use RedirectResponse[status] to describe response
    """
    if isinstance(parameters, tuple):
        status_code, headers = parameters
    else:
        status_code, headers = parameters, {}
    assert isinstance(status_code, int)
    docs = {
        str(status_code): {
            "description": HTTPStatus(status_code).description,
            "headers": {
                "Location": {"schema": {"type": "string"}},
            },
        }
    }
    if headers:
        docs[str(status_code)]["headers"].update(headers)
    return docs


RedirectResponse.__class_getitem__ = redirect_response__class_getitem__  # type: ignore


def file_response__class_getitem__(parameters):
    """
    Use FileResponse[content_type, headers] to describe response
    """
    if isinstance(parameters, tuple):
        content_type, headers = parameters
    else:
        content_type, headers = parameters, {}
    assert isinstance(content_type, str)
    docs = {
        "200": {
            "description": HTTPStatus.OK.description,
            "content": {
                content_type: {"schema": {"type": "string", "format": "binary"}}
            },
        },
        "206": {
            "description": HTTPStatus.PARTIAL_CONTENT.description,
            "content": {
                content_type: {"schema": {"type": "string", "format": "binary"}}
            },
        },
    }
    if headers:
        docs["200"]["headers"] = headers
        docs["206"]["headers"] = headers
    return docs


FileResponse.__class_getitem__ = file_response__class_getitem__  # type: ignore


def json_response__class_getitem__(parameters):
    """
    Use JSONResponse[status, headers, content] to describe response
    """
    if isinstance(parameters, tuple):
        assert len(parameters) in (2, 3)
        if len(parameters) == 2:
            (status_code, headers), content = parameters, {}
        else:
            status_code, headers, content = parameters
    else:
        status_code, headers, content = parameters, {}, {}
    assert isinstance(status_code, int) or status_code == "default"

    docs = {
        str(status_code): {
            "description": HTTPStatus(status_code).description,
        }
    }
    if headers:
        docs[str(status_code)]["headers"] = headers

    if content:
        if isinstance(content, dict) or (
            getattr(content, "__origin__", None) is None
            and safe_issubclass(content, BaseModel)
        ):
            real_content = content
        else:
            real_content = create_model(
                f"ParsingModel[{display_as_type(content)}]", __root__=(content, ...)
            )
        docs[str(status_code)]["content"] = real_content

    return docs


JSONResponse.__class_getitem__ = json_response__class_getitem__  # type: ignore
