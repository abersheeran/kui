from __future__ import annotations

from typing import Any, Mapping

from baize.asgi import SmallResponse
from baize.datastructures import URL
from typing_extensions import Protocol

from .requests import request
from .responses import HttpResponse

__all__ = [
    "BaseTemplates",
    "Jinja2Templates",
]


class BaseTemplates(Protocol):
    def TemplateResponse(
        self,
        name: str,
        context: Mapping[str, Any],
        status_code: int = 200,
        headers: Mapping[str, str] | None = None,
        media_type: str | None = None,
        charset: str | None = None,
    ) -> HttpResponse:
        """
        The subclass must override this method and return
        an instance of a Response object.
        """
        raise NotImplementedError


try:
    import jinja2

    from ..templates import Jinja2TemplatesBase
except ImportError:

    class Jinja2Templates:
        def __init__(self) -> None:
            raise NotImplementedError('Install "jinja2" to use Jinja2Templates')

else:

    class _Jinja2TemplateResponse(SmallResponse):
        media_type = "text/html"

        def __init__(
            self,
            env: jinja2.Environment,
            name: str,
            context: Mapping[str, Any],
            status_code: int = 200,
            headers: Mapping[str, str] | None = None,
            media_type: str | None = None,
            charset: str | None = None,
        ):
            self.env = env
            self.template = self.env.get_template(name)
            super().__init__(context, status_code, headers, media_type, charset)

        async def render(self, context: Mapping[str, Any]) -> bytes:
            if self.env.is_async:
                text = await self.template.render_async(context)
            else:
                text = self.template.render(context)
            return text.encode(self.charset)

    @jinja2.pass_context
    def url_for(context: dict, name: str, path_params: Mapping[str, Any]) -> URL:
        return request.url_for(name, path_params)

    class Jinja2Templates(Jinja2TemplatesBase):  # type: ignore
        """
        templates = Jinja2Templates("dir", "package:dir")

        return templates.TemplateResponse("index.html", {"request": request})
        """

        def __init__(self, *directories: str) -> None:
            super().__init__(*directories)
            self.env.globals["url_for"] = url_for

        def get_env(self, loader: jinja2.BaseLoader) -> jinja2.Environment:
            return jinja2.Environment(loader=loader, enable_async=True, autoescape=True)

        def TemplateResponse(
            self,
            name: str,
            context: Mapping[str, Any],
            status_code: int = 200,
            headers: Mapping[str, str] | None = None,
            media_type: str | None = None,
            charset: str | None = None,
        ) -> _Jinja2TemplateResponse:
            return _Jinja2TemplateResponse(
                self.env,
                name,
                context,
                status_code=status_code,
                headers=headers,
                media_type=media_type,
                charset=charset,
            )
