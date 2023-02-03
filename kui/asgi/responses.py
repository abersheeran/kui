from __future__ import annotations

import typing

from baize import asgi as baize_asgi
from baize.typing import ServerSentEvent
from pydantic.json import pydantic_encoder

from ..responses import (
    FileResponseMixin,
    HTMLResponseMixin,
    JSONResponseMixin,
    PlainTextResponseMixin,
    RedirectResponseMixin,
    SendEventResponseMixin,
    StreamResponseMixin,
)
from .requests import request

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


class JSONResponse(JSONResponseMixin, baize_asgi.JSONResponse):
    def __init__(
        self,
        content: typing.Any,
        status_code: int = 200,
        headers: typing.Optional[typing.Mapping[str, str]] = None,
        **kwargs: typing.Any,
    ) -> None:
        json_kwargs: typing.Dict[str, typing.Any] = {
            "default": pydantic_encoder,
        }
        json_kwargs.update(**kwargs)
        super().__init__(
            content, status_code=status_code, headers=headers, **json_kwargs
        )


class FileResponse(
    FileResponseMixin,
    baize_asgi.FileResponse,
):
    pass


class PlainTextResponse(
    PlainTextResponseMixin,
    baize_asgi.PlainTextResponse,
):
    pass


class HTMLResponse(
    HTMLResponseMixin,
    baize_asgi.HTMLResponse,
):
    pass


class RedirectResponse(
    RedirectResponseMixin,
    baize_asgi.RedirectResponse,
):
    pass


class SendEventResponse(
    SendEventResponseMixin,
    baize_asgi.SendEventResponse,
):
    pass


class StreamResponse(
    StreamResponseMixin,
    baize_asgi.StreamResponse,
):
    pass


def TemplateResponse(
    name: str,
    context: typing.Mapping[str, typing.Any],
    status_code: int = 200,
    headers: typing.Optional[typing.Mapping[str, str]] = None,
    media_type: typing.Optional[str] = None,
    charset: typing.Optional[str] = None,
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
    shortcut for convert response to HttpResponse

    Example:

        response = convert(response)

    It is equivalent to:

        if isinstance(response, tuple):
            response = app.response_converter(*response)
        else:
            response = app.response_converter(response)

    """
    if isinstance(response, tuple):
        return request.app.response_converter(*response)
    else:
        return request.app.response_converter(response)
