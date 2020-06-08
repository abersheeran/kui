import typing
import functools
from importlib import import_module

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
    BackgroundTask,
    _TemplateResponse,
)

from ..utils import Singleton
from ..config import Config

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


class Jinja2Templates:
    def __init__(self, searchpath: typing.Union[str, typing.Iterable[str]]) -> None:
        self.loader = jinja2.FileSystemLoader(searchpath)
        self.env = jinja2.Environment(loader=self.loader, autoescape=True)

    def get_template(self, name: str) -> jinja2.Template:
        return self.env.get_template(name)

    def TemplateResponse(
        self,
        name: str,
        context: dict,
        status_code: int = 200,
        headers: dict = None,
        media_type: str = None,
        background: BackgroundTask = None,
    ) -> _TemplateResponse:
        template = self.get_template(name)
        return _TemplateResponse(
            template,
            context,
            status_code=status_code,
            headers=headers,
            media_type=media_type,
            background=background,
        )


def TemplateResponse(
    name: str,
    context: dict,
    status_code: int = 200,
    headers: dict = None,
    media_type: str = None,
    background: BackgroundTask = None,
) -> _TemplateResponse:
    app = getattr(import_module("..applications", __package__), "Index")()
    return app.templates.TemplateResponse(
        name, context, status_code, headers, media_type, background
    )


class YAMLResponse(Response):
    media_type = "text/yaml"

    def render(self, content: typing.Any) -> bytes:
        return yaml.dump(content, indent=2).encode("utf8")


@functools.singledispatch
def automatic(*args: typing.Any) -> Response:
    # Response or Response subclass
    if isinstance(args[0], Response):
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
    body: typing.Tuple[tuple, list, dict], status: int = 200, headers: dict = None
) -> Response:
    return JSONResponse(body, status, headers)


@automatic.register(str)
@automatic.register(bytes)
def _plain_text(
    body: typing.Union[str, bytes], status: int = 200, headers: dict = None
) -> Response:
    return PlainTextResponse(body, status, headers)
