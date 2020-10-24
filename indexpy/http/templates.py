import typing
from abc import ABCMeta, abstractmethod

import jinja2

from indexpy.types import Receive, Scope, Send

from .background import BackgroundTask
from .responses import Response


class BaseTemplates(metaclass=ABCMeta):
    @abstractmethod
    def TemplateResponse(
        self,
        name: str,
        context: dict,
        status_code: int = 200,
        headers: dict = None,
        media_type: str = None,
        background: BackgroundTask = None,
    ) -> Response:
        """
        The subclass must override this method and return
        an instance of a Response object.
        """


class _Jinja2TemplateResponse(Response):
    media_type = "text/html"

    def __init__(
        self,
        env: jinja2.Environment,
        name: str,
        context: dict,
        status_code: int = 200,
        headers: dict = None,
        media_type: str = None,
        background: BackgroundTask = None,
    ):
        self.env = env
        self.template = self.env.get_template(name)
        self.context = context
        super().__init__(None, status_code, headers, media_type, background)

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if self.env.enable_async:  # type: ignore
            content = await self.template.render_async(self.context)
        else:
            content = self.template.render(self.context)
        self.body = self.render(content)
        self.headers["content-length"] = str(len(self.body))

        extensions = self.context.get("request", {}).get("extensions", {})
        if "http.response.template" in extensions:
            await send(
                {
                    "type": "http.response.template",
                    "template": self.template,
                    "context": self.context,
                }
            )
        await super().__call__(scope, receive, send)


class Jinja2Templates(BaseTemplates):
    """
    templates = Jinja2Templates("templates")

    return templates.TemplateResponse("index.html", {"request": request})
    """

    def __init__(self, *directories: str) -> None:
        self.env = self.get_env(self.get_loaders(*directories))

    def get_loaders(self, *directories: str) -> jinja2.BaseLoader:
        templates_loaders: typing.List[
            typing.Union[jinja2.FileSystemLoader, jinja2.PackageLoader]
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
        def url_for(context: dict, name: str, **path_params: typing.Any) -> str:
            router = context["request"]["app"].router
            return router.url_for(name, path_params)

        env = jinja2.Environment(loader=loader, enable_async=True, autoescape=True)
        env.globals["url_for"] = url_for
        return env

    def TemplateResponse(
        self,
        name: str,
        context: dict,
        status_code: int = 200,
        headers: dict = None,
        media_type: str = None,
        background: BackgroundTask = None,
    ) -> _Jinja2TemplateResponse:

        return _Jinja2TemplateResponse(
            self.env,
            name,
            context,
            status_code=status_code,
            headers=headers,
            media_type=media_type,
            background=background,
        )
