from __future__ import annotations

import json
import typing

from baize import wsgi as baize_wsgi
from baize.typing import ServerSentEvent

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

HttpResponse = baize_wsgi.Response


class JSONResponse(JSONResponseMixin, baize_wsgi.JSONResponse):
    def render(self, content: typing.Any) -> bytes:
        if not self.json_kwargs.get("default"):
            self.json_kwargs["default"] = request.app.json_encoder
        return json.dumps(content, **self.json_kwargs).encode(self.charset)


class FileResponse(
    FileResponseMixin,
    baize_wsgi.FileResponse,
):
    pass


class PlainTextResponse(
    PlainTextResponseMixin,
    baize_wsgi.PlainTextResponse,
):
    pass


class HTMLResponse(
    HTMLResponseMixin,
    baize_wsgi.HTMLResponse,
):
    pass


class RedirectResponse(
    RedirectResponseMixin,
    baize_wsgi.RedirectResponse,
):
    pass


class SendEventResponse(
    SendEventResponseMixin,
    baize_wsgi.SendEventResponse,
):
    pass


class StreamResponse(
    StreamResponseMixin,
    baize_wsgi.StreamResponse,
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
