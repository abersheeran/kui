import os
from copy import deepcopy
from typing import Any, Dict, List, Sequence, cast

from starlette.endpoints import Request, Response

from ..applications import Index
from ..http.responses import HTMLResponse, JSONResponse, YAMLResponse
from ..routing import HttpRoute
from ..types import Literal, TypedDict
from .schema import schema_parameters, schema_request_body, schema_response

Tag = TypedDict("Tag", {"description": str, "paths": Sequence[str]})


class OpenAPI:
    def __init__(
        self,
        title: str,
        description: str,
        version: str,
        *,
        tags: Dict[str, Tag] = {},
        template: str = "",
        media_type: Literal["yaml", "json"] = "yaml",
    ):
        """
        media_type: yaml or json
        """
        assert media_type in ("yaml", "json"), "media_type must in 'yaml' or 'json'"

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

    def _generate_paths(self, app: Index) -> Dict[str, Any]:
        result = {}

        for path_format, endpoint in app.router.http_tree.iterator():
            path_docs = self._generate_path(endpoint, path_format)
            if path_docs:
                result[path_format] = path_docs

        return result

    def _generate_path(self, view: Any, path: str) -> Dict[str, Any]:
        result = {}
        if hasattr(view, "__methods__"):
            for method in view.__methods__:  # type: ignore
                if method == "OPTIONS":
                    continue
                method = method.lower()
                method_docs = self._generate_method(getattr(view, method), path)
                if method_docs:
                    result[method] = method_docs
        elif hasattr(view, "__method__"):
            method_docs = self._generate_method(view, path)
            if method_docs:
                result[view.__method__.lower()] = method_docs
        return result

    def _generate_method(self, func: object, path: str) -> Dict[str, Any]:
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

        params = getattr(func, "__params__", {})
        result["parameters"] = schema_parameters(
            params.get("path"),
            params.get("query"),
            params.get("header"),
            params.get("cookie"),
        )
        if not result["parameters"]:
            del result["parameters"]

        result["requestBody"] = schema_request_body(params.get("body"))
        if not result["requestBody"]:
            del result["requestBody"]

        try:
            resps = getattr(func, "__resps__")
        except AttributeError:
            pass
        else:
            result["responses"] = {}
            for status, content in resps.items():
                result["responses"][int(status)] = {
                    "description": content["description"],
                }
                if content["model"] is not None:
                    result["responses"][status]["content"] = schema_response(
                        content["model"]
                    )
            if not result["responses"]:
                del result["responses"]

        if result and path in self.path2tag:  # has openapi docs, add tags
            result["tags"] = self.path2tag[path]

        return result

    def create_docs(self, request: Request) -> dict:
        openapi: dict = deepcopy(self.openapi)
        openapi["servers"] = [
            {
                "url": f"{request.url.scheme}://{request.url.netloc}",
                "description": "Current server",
            }
        ]
        openapi["paths"] = self._generate_paths(cast(Index, request["app"]))

        return openapi

    @property
    def routes(self) -> List[HttpRoute]:
        async def template(request: Request) -> Response:
            if self.html_template:
                return HTMLResponse(self.html_template)

            with open(
                os.path.join(
                    os.path.dirname(os.path.abspath(__file__)), "template.html"
                )
            ) as file:
                DEFAULT_TEMPLATE = file.read()
            return HTMLResponse(DEFAULT_TEMPLATE)

        async def docs(request: Request) -> Response:
            openapi = self.create_docs(request)
            media_type = request.query_params.get("type") or self.media_type

            if media_type == "json":
                return JSONResponse(openapi)
            return YAMLResponse(openapi)

        return [
            HttpRoute("/", template, name=None, method="get"),
            HttpRoute("/get", docs, name=None, method="get"),
        ]
