from __future__ import annotations

from abc import ABCMeta, abstractmethod
from typing import Any, List, Mapping, Union

from baize.asgi import SmallResponse

from .requests import request
from .responses import HttpResponse


class BaseTemplates(metaclass=ABCMeta):
    @abstractmethod
    def TemplateResponse(
        self,
        name: str,
        context: Mapping[str, Any],
        status_code: int = 200,
        headers: Mapping[str, str] = None,
        media_type: str = None,
        charset: str = None,
    ) -> HttpResponse:
        """
        The subclass must override this method and return
        an instance of a Response object.
        """


try:
    import jinja2
except ImportError:
    pass
else:

    class _Jinja2TemplateResponse(SmallResponse):
        media_type = "text/html"

        def __init__(
            self,
            env: jinja2.Environment,
            name: str,
            context: Mapping[str, Any],
            status_code: int = 200,
            headers: Mapping[str, str] = None,
            media_type: str = None,
            charset: str = None,
        ):
            self.env = env
            self.template = self.env.get_template(name)
            super().__init__(context, status_code, headers, media_type, charset)

        async def render(self, context: Mapping[str, Any]) -> bytes:
            if self.env.enable_async:  # type: ignore
                text = await self.template.render_async(context)
            else:
                text = self.template.render(context)
            return text.encode(self.charset)

    class Jinja2Templates(BaseTemplates):
        """
        templates = Jinja2Templates("dir", "package:dir")

        return templates.TemplateResponse("index.html", {"request": request})
        """

        def __init__(self, *directories: str) -> None:
            self.env = self.get_env(self.get_loaders(*directories))

        def get_loaders(self, *directories: str) -> jinja2.BaseLoader:
            templates_loaders: List[
                Union[jinja2.FileSystemLoader, jinja2.PackageLoader]
            ] = []
            for directory in directories:
                if ":" in directory:
                    package_name, package_path = directory.split(":", maxsplit=1)
                    templates_loaders.append(
                        jinja2.PackageLoader(package_name, package_path)
                    )
                else:
                    templates_loaders.append(jinja2.FileSystemLoader(directory))
            return jinja2.ChoiceLoader(templates_loaders)

        def get_env(self, loader: jinja2.BaseLoader) -> jinja2.Environment:
            @jinja2.contextfunction
            def url_for(context: dict, name: str, **path_params: Any) -> str:
                router = request.app.router
                return router.url_for(name, path_params)

            env = jinja2.Environment(loader=loader, enable_async=True, autoescape=True)
            env.globals["url_for"] = url_for
            return env

        def TemplateResponse(
            self,
            name: str,
            context: Mapping[str, Any],
            status_code: int = 200,
            headers: Mapping[str, str] = None,
            media_type: str = None,
            charset: str = None,
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
