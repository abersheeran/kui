from __future__ import annotations

import typing

from baize.asgi import FileResponse, HTMLResponse
from baize.asgi import JSONResponse as _JSONResponse
from baize.asgi import PlainTextResponse, RedirectResponse
from baize.asgi import Response as HttpResponse
from baize.asgi import SendEventResponse, ServerSentEvent, StreamResponse
from pydantic.json import pydantic_encoder

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
) -> HttpResponse:
    templates = request.app.templates
    if templates is None:
        raise RuntimeError(
            "You must assign a value to `app.templates` to use TemplateResponse"
        )

    return templates.TemplateResponse(name, context, status_code, headers)


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
        return request.app.response_convertor(*response)
    else:
        return request.app.response_convertor(response)
