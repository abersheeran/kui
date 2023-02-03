from __future__ import annotations

import typing
from http import HTTPStatus

from pydantic import BaseModel, create_model
from pydantic.typing import display_as_type

from .utils import safe_issubclass


class JSONResponseMixin:
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
            if isinstance(content, dict):
                real_content = {"application/json": {"schema": content}}
            elif getattr(content, "__origin__", None) is None and safe_issubclass(
                content, BaseModel
            ):
                real_content = content
            else:
                real_content = create_model(
                    f"ParsingModel[{display_as_type(content)}]", __root__=(content, ...)
                )
            docs[str(status_code)]["content"] = real_content

        return docs


class FileResponseMixin:
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


class PlainTextResponseMixin:
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


class HTMLResponseMixin:
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


class RedirectResponseMixin:
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


class SendEventResponseMixin:
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


class StreamResponseMixin:
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
