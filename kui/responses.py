from __future__ import annotations

import abc
import typing
from http import HTTPStatus

from pydantic import BaseModel

from .openapi import specification as spec
from .pydantic_compatible import create_root_model, to_jsonable_python
from .utils import safe_issubclass


def _json_encoder(obj: typing.Any) -> typing.Any:
    return to_jsonable_python(obj)


class JSONResponseDocsMetaclass(abc.ABCMeta):
    def __getitem__(
        cls,
        parameters: typing.Tuple[
            int,
            typing.Dict[str, spec.Header | spec.Reference],
            typing.Type[BaseModel] | spec.Schema | type,
        ]
        | typing.Tuple[int, typing.Dict[str, spec.Header | spec.Reference]]
        | int,
    ) -> spec.Responses:
        """
        Use JSONResponse[status, headers, content] to describe response
        """
        status_code: int
        headers: typing.Dict[str, spec.Header | spec.Reference]
        content: typing.Type[BaseModel] | spec.Schema | typing.Any

        if isinstance(parameters, tuple):
            assert len(parameters) in (2, 3)
            # mypy can't check this
            if len(parameters) == 2:
                (status_code, headers), content = parameters, {}  # type: ignore
            else:
                status_code, headers, content = parameters  # type: ignore
        else:
            status_code, headers, content = parameters, {}, {}
        assert isinstance(status_code, int) or status_code == "default"

        docs: typing.Dict[str, typing.Any] = {
            str(status_code): {
                "description": HTTPStatus(status_code).description,
                "headers": headers,
            }
        }

        if content:
            real_content: (
                spec.Schema
                | typing.Type[BaseModel]
                | typing.Dict[typing.Any, typing.Any]
            )
            if isinstance(content, dict):
                real_content = content
            elif getattr(content, "__origin__", None) is None and safe_issubclass(
                content, BaseModel
            ):
                real_content = content
            else:
                real_content = create_root_model(content)
            docs[str(status_code)]["content"] = {
                "application/json": {"schema": real_content}
            }

        return docs


class JSONResponseMixin(metaclass=JSONResponseDocsMetaclass):
    """
    JSON response with OpenAPI docs support
    """


class FileResponseDocsMetaclass(abc.ABCMeta):
    def __getitem__(
        cls,
        parameters: typing.Tuple[str, typing.Dict[str, spec.Header | spec.Reference]]
        | str,
    ) -> spec.Responses:
        """
        Use FileResponse[content_type, headers] to describe response
        """
        if isinstance(parameters, tuple):
            content_type, headers = parameters
        else:
            content_type, headers = parameters, {}
        assert isinstance(content_type, str)

        return {
            "200": {
                "description": HTTPStatus.OK.description,
                "content": {
                    content_type: {"schema": {"type": "string", "format": "binary"}}
                },
                "headers": headers,
            },
            "206": {
                "description": HTTPStatus.PARTIAL_CONTENT.description,
                "content": {
                    content_type: {"schema": {"type": "string", "format": "binary"}}
                },
                "headers": headers,
            },
        }


class FileResponseMixin(metaclass=FileResponseDocsMetaclass):
    """
    File response with OpenAPI docs support
    """


class PlainTextResponseDocsMetaclass(abc.ABCMeta):
    def __getitem__(
        cls,
        parameters: typing.Tuple[int, typing.Dict[str, spec.Header | spec.Reference]]
        | int,
    ) -> spec.Responses:
        """
        Use PlainTextResponse[status, headers] to describe response
        """
        if isinstance(parameters, tuple):
            status_code, headers = parameters
        else:
            status_code, headers = parameters, {}
        assert isinstance(status_code, int)

        return {
            str(status_code): {
                "description": HTTPStatus(status_code).description,
                "content": {"text/plain": {"schema": {"type": "string"}}},
                "headers": headers,
            }
        }


class PlainTextResponseMixin(metaclass=PlainTextResponseDocsMetaclass):
    """
    Plain text response with OpenAPI docs support
    """


class HTMLResponseDocsMetaclass(abc.ABCMeta):
    def __getitem__(
        cls,
        parameters: typing.Tuple[int, typing.Dict[str, spec.Header | spec.Reference]]
        | int,
    ) -> spec.Responses:
        """
        Use HTMLResponse[status, headers] to describe response
        """
        if isinstance(parameters, tuple):
            status_code, headers = parameters
        else:
            status_code, headers = parameters, {}
        assert isinstance(status_code, int)

        return {
            str(status_code): {
                "description": HTTPStatus(status_code).description,
                "content": {"text/html": {"schema": {"type": "string"}}},
                "headers": headers,
            }
        }


class HTMLResponseMixin(metaclass=HTMLResponseDocsMetaclass):
    """
    HTML response with OpenAPI docs support
    """


class RedirectResponseDocsMetaclass(abc.ABCMeta):
    def __getitem__(
        cls,
        parameters: typing.Tuple[int, typing.Dict[str, spec.Header | spec.Reference]]
        | int,
    ) -> spec.Responses:
        """
        Use RedirectResponse[status, headers] to describe response
        """
        if isinstance(parameters, tuple):
            status_code, headers = parameters
        else:
            status_code, headers = parameters, {}
        assert isinstance(status_code, int)

        return {
            str(status_code): {
                "description": HTTPStatus(status_code).description,
                "headers": {
                    "Location": {"schema": {"type": "string"}},
                    **headers,
                },
            }
        }


class RedirectResponseMixin(metaclass=RedirectResponseDocsMetaclass):
    """
    Redirect response with OpenAPI docs support
    """


class SendEventResponseDocsMetaclass(abc.ABCMeta):
    def __getitem__(
        cls,
        parameters: typing.Tuple[int, typing.Dict[str, spec.Header | spec.Reference]]
        | int,
    ) -> spec.Responses:
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
        return {
            str(status_code): {
                "description": HTTPStatus(status_code).description,
                "content": {"text/event-stream": {"schema": {"type": "string"}}},
                "headers": headers,
            }
        }


class SendEventResponseMixin(metaclass=SendEventResponseDocsMetaclass):
    """
    Send event response with OpenAPI docs support
    """


class StreamResponseDocsMetaclass(abc.ABCMeta):
    def __getitem__(
        cls,
        parameters: typing.Tuple[int, typing.Dict[str, spec.Header | spec.Reference]]
        | int,
    ) -> spec.Responses:
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
        return {
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


class StreamResponseMixin(metaclass=StreamResponseDocsMetaclass):
    """
    Stream response with OpenAPI docs support
    """
