import os
import importlib
from inspect import signature

from starlette.types import Scope, Receive, Send
from starlette.endpoints import Request, Response
from starlette.exceptions import HTTPException

from index.responses import PlainTextResponse, JSONResponse, YAMLResponse
from index.config import config

from .models import Model, Query


def get_views():
    views_path = os.path.join(config.path, "views").replace("\\", "/")
    for root, _, files in os.walk(views_path):
        for file in files:
            if not file.endswith(".py"):
                continue
            if file == "__init__.py":
                continue
            abspath = os.path.join(root, file)
            relpath = os.path.relpath(abspath, config.path).replace("\\", "/")
            module_name = relpath[:-3].replace("/", ".")
            module = importlib.import_module(module_name)
            path = relpath[len("views") : -3]
            if path.endswith("index"):
                path = path[: -len("index")]
            if abspath.startswith(views_path):
                yield path, module


class OpenAPI:
    def __init__(
        self, title: str, description: str, version: str, *, media_type="yaml"
    ):
        """
        media_type: yaml or json
        """
        assert media_type in ("yaml", "json"), "media_type must in 'yaml' or 'json'"

        info = {"title": title, "description": description, "version": version}
        self.openapi = {"openapi": "3.0.0", "info": info, "paths": {}}
        self.media_type = media_type

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            raise HTTPException(404)
        request = Request(scope, receive, send)
        handler_name = "get" if request.method == "HEAD" else request.method.lower()
        handler = getattr(self, handler_name, self.method_not_allowed)
        response = await handler(request)
        await response(scope, receive, send)

    async def method_not_allowed(self, request: Request) -> Response:
        # If we're running inside a starlette application then raise an
        # exception, so that the configurable exception handler can deal with
        # returning the response. For plain ASGI apps, just return the response.
        if "app" in request.scope:
            raise HTTPException(status_code=405)
        return PlainTextResponse("Method Not Allowed", status_code=405)

    async def get(self, request: Request) -> Response:
        return await self.post(request)

    async def post(self, request: Request) -> Response:
        paths = self.openapi["paths"]
        for path, view in get_views():
            viewclass = view.HTTP()
            paths[path] = {}
            for method in viewclass.allowed_methods():
                if method == "OPTIONS":
                    continue
                method = method.lower()
                sig = signature(getattr(viewclass, method))
                doc = getattr(viewclass, method).__doc__
                if isinstance(doc, str):
                    doc = doc.strip()
                    paths[path][method] = {
                        "summary": doc.splitlines()[0],
                        "description": "\n".join(doc.splitlines()[1:]).strip(),
                    }

                query = sig.parameters.get("query")
                if query and issubclass(query.annotation, Query):
                    paths[path][method]["parameters"] = query.annotation.openapi()

                body = sig.parameters.get("body")
                if body and issubclass(body.annotation, Model):
                    paths[path][method]["requestBody"] = {
                        "required": True,
                        "content": {
                            body.annotation.get_content_type(): {
                                "schema": body.annotation.openapi()
                            }
                        },
                    }

            if not paths[path]:
                del paths[path]

        if self.media_type == "yaml" or request.query_params.get("type") == "yaml":
            return YAMLResponse(self.openapi)

        if self.media_type == "json" or request.query_params.get("type") == "json":
            return JSONResponse(self.openapi)
