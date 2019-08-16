"""
Maybe more repsonse type will be done in the future
"""
import typing
import functools

from starlette.background import BackgroundTask
from starlette.responses import (
    Response,
    HTMLResponse,
    PlainTextResponse,
    JSONResponse,
    RedirectResponse,
    StreamingResponse,
    FileResponse
)
from starlette.templating import Jinja2Templates

from .types import typeassert

__all__ = [
    "register_type",
    "Response",
    "HTMLResponse",
    "PlainTextResponse",
    "JSONResponse",
    "RedirectResponse",
    "StreamingResponse",
    "FileResponse",
    "TemplateResponse",
]


TemplateResponse = Jinja2Templates(directory='templates').TemplateResponse


class AutoResponseType:

    type_map = {}

    @classmethod
    def register_type(cls, type_: typing.Any) -> typing.Callable:
        def register_func(func: typing.Callable) -> typing.Callable:
            cls.type_map[type_] = func

            def wrapper(*args, **kwargs) -> Response:
                return func(*args, **kwargs)
            return wrapper
        return register_func

    @classmethod
    def automatic(cls, *args) -> Response:

        # Response or Response subclass
        if isinstance(args[0], Response):
            return args[0]

        try:
            return cls.type_map[type(args[0])](*args)
        except KeyError:
            raise TypeError(f"Cannot find automatic handler for this type: {type(args[0])}")


register_type = functools.partial(AutoResponseType.register_type)
automatic = functools.partial(AutoResponseType.automatic)


@register_type(dict)
@typeassert
def json_type(
    body: dict,
    status: int = 200,
    headers: dict = None,
    background: BackgroundTask = None
) -> Response:

    return JSONResponse(
        body,
        status,
        headers,
        background=background
    )


@register_type(str)
@typeassert
def text_type(
    body: str,
    status: int = 200,
    headers: dict = None,
    background: BackgroundTask = None
) -> Response:

    return PlainTextResponse(
        body,
        status,
        headers,
        background=background
    )
