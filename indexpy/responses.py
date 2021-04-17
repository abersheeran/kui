from __future__ import annotations

import functools
import typing
from types import AsyncGeneratorType

from baize.asgi import (
    FileResponse,
    HTMLResponse,
    JSONResponse,
    PlainTextResponse,
    RedirectResponse,
)
from baize.asgi import Response as HttpResponse
from baize.asgi import SendEventResponse, ServerSentEvent, StreamResponse

from .requests import request

__all__ = [
    "automatic",
    "convert_response",
    "HttpResponse",
    "FileResponse",
    "HTMLResponse",
    "JSONResponse",
    "PlainTextResponse",
    "RedirectResponse",
    "SendEventResponse",
    "StreamResponse",
    "TemplateResponse",
]


def TemplateResponse(
    name: str, context: dict, status_code: int = 200, headers: dict = None
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
        return automatic(*response)
    else:
        return automatic(response)


@functools.singledispatch
def automatic(*args: typing.Any) -> HttpResponse:
    # Response or Response subclass
    if isinstance(args[0], HttpResponse):
        return args[0]

    raise TypeError(f"Cannot find automatic handler for this type: {type(args[0])}")


@automatic.register(type(None))
def _none(ret: typing.Type[None]) -> typing.NoReturn:
    raise TypeError(
        "Get 'None'. Maybe you need to add a return statement to the function."
    )


@automatic.register(tuple)
@automatic.register(list)
@automatic.register(dict)
def _json(
    body, status: int = 200, headers: typing.Mapping[str, str] = None
) -> HttpResponse:
    return JSONResponse(body, status, headers)


@automatic.register(str)
@automatic.register(bytes)
def _plain_text(
    body: typing.Union[str, bytes],
    status: int = 200,
    headers: typing.Mapping[str, str] = None,
) -> HttpResponse:
    return PlainTextResponse(body, status, headers)


@automatic.register(AsyncGeneratorType)
def _send_event(
    generator: typing.AsyncGenerator[ServerSentEvent, None],
    status: int = 200,
    headers: typing.Mapping[str, str] = None,
) -> HttpResponse:
    return SendEventResponse(generator, status, headers)
