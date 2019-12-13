import typing
import functools

import yaml
from starlette.responses import (
    Response,
    HTMLResponse,
    PlainTextResponse,
    JSONResponse,
    RedirectResponse,
    StreamingResponse,
    FileResponse,
)
from starlette.templating import Jinja2Templates

__all__ = [
    "automatic",
    "Response",
    "HTMLResponse",
    "PlainTextResponse",
    "JSONResponse",
    "YAMLResponse",
    "RedirectResponse",
    "StreamingResponse",
    "FileResponse",
    "TemplateResponse",
]


TemplateResponse = Jinja2Templates(directory="templates").TemplateResponse


class YAMLResponse(Response):
    media_type = "text/yaml"

    def render(self, content: typing.Any) -> bytes:
        return yaml.dump(content, indent=2).encode("utf8")


@functools.singledispatch
def automatic(*args) -> Response:
    # Response or Response subclass
    if isinstance(args[0], Response):
        return args[0]

    raise TypeError(f"Cannot find automatic handler for this type: {type(args[0])}")


@automatic.register(dict)
def _automatic(body: typing.Dict, status: int = 200, headers: dict = None) -> Response:
    return JSONResponse(body, status, headers)


@automatic.register(str)
@automatic.register(bytes)
def _automatic(
    body: typing.Union[str, bytes], status: int = 200, headers: dict = None
) -> Response:
    return PlainTextResponse(body, status, headers)
