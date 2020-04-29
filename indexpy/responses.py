import typing
import functools

import yaml
import jinja2
from starlette.responses import (
    Response,
    HTMLResponse,
    PlainTextResponse,
    JSONResponse,
    RedirectResponse,
    StreamingResponse,
    FileResponse,
)
from starlette.templating import (
    Jinja2Templates as _Jinja2Templates,
    BackgroundTask,
    _TemplateResponse,
)

from .utils import Singleton
from .config import Config

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


class Jinja2Templates(_Jinja2Templates, metaclass=Singleton):
    def __init__(self) -> None:
        self.env = self.get_env(Config().TEMPLATES)

    def get_env(self, directory: str) -> jinja2.Environment:
        loader = jinja2.FileSystemLoader(directory)
        env = jinja2.Environment(loader=loader, autoescape=True)
        return env


def TemplateResponse(
    name: str,
    context: dict,
    status_code: int = 200,
    headers: dict = None,
    media_type: str = None,
    background: BackgroundTask = None,
) -> _TemplateResponse:
    return Jinja2Templates().TemplateResponse(
        name, context, status_code, headers, media_type, background
    )


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


@automatic.register(type(None))
def _none(ret: typing.Type[None]) -> typing.NoReturn:
    raise TypeError(
        "Get 'None'. Maybe you need to add a return statement to the function."
    )


@automatic.register(dict)
def _json(body: typing.Dict, status: int = 200, headers: dict = None) -> Response:
    return JSONResponse(body, status, headers)


@automatic.register(str)
@automatic.register(bytes)
def _plain_text(
    body: typing.Union[str, bytes], status: int = 200, headers: dict = None
) -> Response:
    return PlainTextResponse(body, status, headers)
