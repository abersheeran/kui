import os
import importlib
from copy import deepcopy
from inspect import signature

from starlette.types import Scope, Receive, Send
from starlette.endpoints import Request, Response
from starlette.exceptions import HTTPException

from index.responses import (
    JSONResponse,
    YAMLResponse,
    HTMLResponse,
)
from index.config import config

from .models import Model
from .functions import Schema


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
        self,
        title: str,
        description: str,
        version: str,
        *,
        template: str = "",
        media_type="yaml",
    ):
        """
        media_type: yaml or json
        """
        assert media_type in ("yaml", "json"), "media_type must in 'yaml' or 'json'"

        info = {"title": title, "description": description, "version": version}
        self.openapi = {"openapi": "3.0.0", "info": info, "paths": {}}
        self.html_template = template
        self.media_type = media_type

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http" or scope["path"] not in ("/", "/get"):
            raise HTTPException(404)
        request = Request(scope, receive, send)

        if scope["path"] == "/get":
            handler = getattr(self, "docs")
        elif scope["path"] == "/":
            handler = getattr(self, "template")
        response = await handler(request)
        await response(scope, receive, send)

    async def template(self, request: Request) -> Response:
        if self.html_template:
            return HTMLResponse(self.html_template)
        return HTMLResponse(DEFAULT_TEMPLATE)

    async def docs(self, request: Request) -> Response:
        openapi = deepcopy(self.openapi)
        openapi["servers"] = [
            {
                "url": f"{request.url.scheme}://{request.url.netloc}",
                "description": "Current server",
            }
        ]

        paths = openapi["paths"]
        for path, view in get_views():
            if not hasattr(view, "HTTP"):
                continue
            viewclass = view.HTTP()
            paths[path] = {}
            for method in viewclass.allowed_methods():
                if method == "OPTIONS":
                    continue
                method = method.lower()

                sig = signature(getattr(viewclass, method))
                paths[path][method] = {}

                doc = getattr(viewclass, method).__doc__
                if isinstance(doc, str):
                    doc = doc.strip()
                    paths[path][method].update(
                        {
                            "summary": doc.splitlines()[0],
                            "description": "\n".join(doc.splitlines()[1:]).strip(),
                        }
                    )

                query = sig.parameters.get("query")
                if query and issubclass(query.annotation, Model):
                    paths[path][method]["parameters"] = Schema.in_query(
                        query.annotation
                    )

                body = sig.parameters.get("body")
                if body and issubclass(body.annotation, Model):
                    paths[path][method]["requestBody"] = {
                        "required": True,
                        "content": {
                            body.annotation.content_type: {
                                "schema": Schema.request_body(body.annotation)
                            }
                        },
                    }
                    description = body.annotation.__doc__
                    if description:
                        paths[path][method]["requestBody"]["description"] = description

                try:
                    resps = getattr(getattr(viewclass, method), "__resps__")
                except AttributeError:
                    pass
                else:
                    repsonses = paths[path][method]["responses"] = {}
                    for status, content in resps.items():
                        repsonses[status] = {
                            "description": content["description"],
                        }
                        if content["model"] is not None:
                            repsonses[status]["content"] = {
                                content["model"].content_type: {
                                    "schema": Schema.response(content["model"])
                                }
                            }

                if not paths[path][method]:
                    del paths[path][method]

            if not paths[path]:
                del paths[path]

        if self.media_type == "yaml" or request.query_params.get("type") == "yaml":
            return YAMLResponse(openapi)

        if self.media_type == "json" or request.query_params.get("type") == "json":
            return JSONResponse(openapi)


DEFAULT_TEMPLATE = """
<!DOCTYPE html>
<html>
  <head>
    <title>OpenAPI power by Index.py</title>
    <!-- needed for adaptive design -->
    <meta charset="utf-8"/>
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <link href="https://fonts.googleapis.com/css?family=Montserrat:300,400,700|Roboto:300,400,700" rel="stylesheet">

    <style>
      body {
        margin: 0;
        padding: 0;
      }
    </style>
  </head>
  <body>
    <redoc spec-url='get'></redoc>
    <script src="https://cdn.jsdelivr.net/npm/redoc@next/bundles/redoc.standalone.js"> </script>
  </body>
</html>
"""
