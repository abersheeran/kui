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
from index.utils import get_views

from .models import Model
from .schema import schema_parameters, schema_request_body, schema_response


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
        else:
            raise HTTPException(404)
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
        for view, path in get_views():
            if not hasattr(view, "HTTP"):
                continue
            viewclass = view.HTTP
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

                paths[path][method]["parameters"] = schema_parameters(
                    None,
                    sig.parameters.get("query").annotation
                    if sig.parameters.get("query")
                    else None,
                    sig.parameters.get("header").annotation
                    if sig.parameters.get("header")
                    else None,
                    sig.parameters.get("cookie").annotation
                    if sig.parameters.get("cookie")
                    else None,
                )
                if not paths[path][method]["parameters"]:
                    del paths[path][method]["parameters"]

                paths[path][method]["requestBody"] = schema_request_body(
                    sig.parameters.get("body").annotation
                    if sig.parameters.get("body")
                    else None
                )
                if not paths[path][method]["requestBody"]:
                    del paths[path][method]["requestBody"]

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
                            repsonses[status]["content"] = schema_response(
                                content["model"]
                            )

                if not paths[path][method]:
                    del paths[path][method]

            if not paths[path]:
                del paths[path]

        media_type = request.query_params.get("type") or self.media_type

        if media_type == "yaml":
            return YAMLResponse(openapi)

        if media_type == "json":
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
