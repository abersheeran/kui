from __future__ import annotations

import typing
from http import HTTPStatus

from baize import asgi as baize_asgi
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

HttpResponse = baize_asgi.Response
ServerSentEvent = baize_asgi.ServerSentEvent


class JSONResponse(baize_asgi.JSONResponse):
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

    def __class_getitem__(cls, parameters: typing.Tuple[typing.Any, ...]):
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

        docs: typing.Dict[str, typing.Any] = {
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


class FileResponse(baize_asgi.FileResponse):
    def __class_getitem__(cls, parameters: typing.Tuple[typing.Any, ...]):
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


class PlainTextResponse(baize_asgi.PlainTextResponse):
    def __class_getitem__(cls, parameters: typing.Tuple[typing.Any, ...]):
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


class HTMLResponse(baize_asgi.HTMLResponse):
    def __class_getitem__(cls, parameters: typing.Tuple[typing.Any, ...]):
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


class RedirectResponse(baize_asgi.RedirectResponse):
    def __class_getitem__(cls, parameters: typing.Tuple[typing.Any, ...]):
        """
        Use RedirectResponse[status, headers] to describe response
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
                    **headers,
                },
            }
        }
        return docs


class SendEventResponse(baize_asgi.SendEventResponse):
    def __class_getitem__(cls, parameters: typing.Tuple[typing.Any, ...]):
        """
        Use SendEventResponse[status, headers] to describe response
        """
        if isinstance(parameters, tuple):
            status_code, headers = parameters
        else:
            status_code, headers = parameters, {}
        assert isinstance(status_code, int)

        # TODO: Follow the spec
        # https://github.com/OAI/OpenAPI-Specification/issues/396
        docs = {
            str(status_code): {
                "description": HTTPStatus(status_code).description,
                "content": {"text/event-stream": {"schema": {"type": "string"}}},
            }
        }
        if headers:
            docs[str(status_code)]["headers"] = headers
        return docs


class StreamResponse(baize_asgi.StreamResponse):
    def __class_getitem__(cls, parameters: typing.Tuple[typing.Any, ...]):
        """
        Use StreamResponse[status, headers] to describe response
        """
        if isinstance(parameters, tuple):
            status_code, headers = parameters
        else:
            status_code, headers = parameters, {}
        assert isinstance(status_code, int)

        # TODO: Follow the spec
        # https://github.com/OAI/OpenAPI-Specification/issues/1576
        docs = {
            str(status_code): {
                "description": HTTPStatus(status_code).description,
                "headers": {
                    "Transfer-Encoding": {
                        "schema": {"type": "string"},
                        "description": "chunked",
                    },
                    **headers,
                },
            }
        }
        return docs


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
