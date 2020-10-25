import os
from copy import deepcopy
from typing import Any, Dict, List, Sequence

from starlette.endpoints import Request, Response

from indexpy.http.responses import HTMLResponse, JSONResponse, YAMLResponse
from indexpy.routing import HttpRoute
from indexpy.types import Literal, TypedDict

from .functions import merge_openapi_info
from .schema import schema_parameter, schema_request_body, schema_response

Tag = TypedDict("Tag", {"description": str, "paths": Sequence[str]})


class OpenAPI:
    def __init__(
        self,
        title: str,
        description: str,
        version: str,
        *,
        tags: Dict[str, Tag] = {},
        template_name: Literal["redoc", "swagger"] = "swagger",
        template: str = "",
        media_type: Literal["yaml", "json"] = "yaml",
    ) -> None:
        if template == "":
            with open(
                os.path.join(
                    os.path.dirname(os.path.abspath(__file__)), f"{template_name}.html"
                ),
                encoding="utf8",
            ) as file:
                template = file.read()

        self.html_template = template
        self.media_type = media_type

        info = {"title": title, "description": description, "version": version}
        self.openapi = {
            "openapi": "3.0.0",
            "info": info,
            "paths": {},
            "tags": [
                {"name": tag_name, "description": tag_info.get("description", "")}
                for tag_name, tag_info in tags.items()
            ],
        }
        self.path2tag: Dict[str, List[str]] = {}
        for tag_name, tag_info in tags.items():
            for path in tag_info["paths"]:
                if path in self.path2tag:
                    self.path2tag[path].append(tag_name)
                else:
                    self.path2tag[path] = [tag_name]

    def _generate_paths(self, app: Any, definitions: dict) -> Dict[str, Any]:
        result = {}

        for path_format, endpoint in app.router.http_tree.iterator():
            path_docs = self._generate_path(endpoint.__raw__, path_format, definitions)
            if not path_docs:
                continue
            result[path_format] = path_docs

        return result

    def _generate_path(self, view: Any, path: str, definitions: dict) -> Dict[str, Any]:
        result = {}
        if hasattr(view, "__methods__"):
            for method in view.__methods__:  # type: ignore
                if method == "OPTIONS":
                    continue
                method = method.lower()
                method_docs = self._generate_method(
                    getattr(view, method), path, definitions
                )
                if not method_docs:
                    continue
                result[method] = method_docs
        elif hasattr(view, "__method__"):
            method_docs = self._generate_method(view, path, definitions)
            if method_docs:
                result[view.__method__.lower()] = method_docs
        return result

    def _generate_method(
        self, func: object, path: str, definitions: dict
    ) -> Dict[str, Any]:
        result: Dict[str, Any] = {}

        doc = func.__doc__
        if isinstance(doc, str):
            doc = doc.strip()
            result.update(
                {
                    "summary": doc.splitlines()[0],
                    "description": "\n".join(doc.splitlines()[1:]).strip(),
                }
            )
        # generate params schema
        __parameters__ = getattr(func, "__parameters__", {})
        parameters = (
            schema_parameter(__parameters__.get("path"), "path")
            + schema_parameter(__parameters__.get("query"), "query")
            + schema_parameter(__parameters__.get("header"), "header")
            + schema_parameter(__parameters__.get("cookie"), "cookie")
        )
        if parameters:
            result["parameters"] = parameters
        # generate request body schema
        request_body, _definitions = schema_request_body(
            getattr(func, "__request_body__", None)
        )
        if request_body:
            result["requestBody"] = request_body
        definitions.update(_definitions)
        # generate responses schema
        __responses__ = getattr(func, "__responses__", {})
        responses: Dict[int, Any] = {}
        for status, info in __responses__.items():
            _ = responses[int(status)] = dict(info)
            if _.get("content") is not None:
                _["content"], _definitions = schema_response(_["content"])
                definitions.update(_definitions)
        if responses:
            result["responses"] = responses
        # set path tags
        if result and path in self.path2tag:
            result["tags"] = self.path2tag[path]
        # merge user custom operation info
        return merge_openapi_info(result, getattr(func, "__extra_docs__", {}))

    def create_docs(self, request: Request) -> dict:
        openapi: dict = deepcopy(self.openapi)
        definitions: Dict[str, Any] = {}
        openapi["servers"] = [
            {
                "url": f"{request.url.scheme}://{request.url.netloc}",
                "description": "Current server",
            }
        ]
        openapi["paths"] = self._generate_paths(request["app"], definitions)
        openapi["definitions"] = definitions
        return openapi

    @property
    def routes(self) -> List[HttpRoute]:
        async def template(request: Request) -> Response:
            return HTMLResponse(self.html_template)

        async def docs(request: Request) -> Response:
            openapi = self.create_docs(request)
            media_type = request.query_params.get("type", self.media_type)

            if media_type == "json":
                return JSONResponse(openapi)
            return YAMLResponse(openapi)

        return [
            HttpRoute("/", template, method="get"),
            HttpRoute("/docs", docs, method="get"),
        ]
