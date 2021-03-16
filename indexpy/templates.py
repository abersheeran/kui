from __future__ import annotations

from abc import ABCMeta, abstractmethod
from typing import Any, List, Mapping, Union

from baize.asgi import Receive, Scope, Send

from .requests import request
from .responses import Response


class BaseTemplates(metaclass=ABCMeta):
    @abstractmethod
    def TemplateResponse(
        self,
        name: str,
        context: dict,
        status_code: int = 200,
        headers: Mapping[str, str] = None,
    ) -> Response:
        """
        The subclass must override this method and return
        an instance of a Response object.
        """


try:
    import jinja2
except ImportError:
    pass
else:

    class _Jinja2TemplateResponse(Response):
        def __init__(
            self,
            env: jinja2.Environment,
            name: str,
            context: dict,
            status_code: int = 200,
            headers: Mapping[str, str] = None,
        ):
            self.env = env
            self.template = self.env.get_template(name)
            self.context = context
            super().__init__(status_code, headers)

        async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
            if self.env.enable_async:  # type: ignore
                content = await self.template.render_async(self.context)
            else:
                content = self.template.render(self.context)

            body = content.encode("utf-8")
            self.raw_headers.append(("content-length", str(len(body))))
            self.raw_headers.append(("content-type", "text/html; charset=utf-8"))

            await send(
                {
                    "type": "http.response.start",
                    "status": self.status_code,
                    "headers": [
                        (k.encode("latin-1"), v.encode("latin-1"))
                        for k, v in self.raw_headers
                    ],
                }
            )
            await send({"type": "http.response.body", "body": body})

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
            context: dict,
            status_code: int = 200,
            headers: Mapping[str, str] = None,
        ) -> _Jinja2TemplateResponse:

            return _Jinja2TemplateResponse(
                self.env, name, context, status_code=status_code, headers=headers
            )
