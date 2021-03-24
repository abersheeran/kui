from __future__ import annotations

import operator
import sys
import typing
from copy import deepcopy
from functools import reduce
from pathlib import Path
from typing import Any, Dict, List, Sequence

if sys.version_info[:2] < (3, 8):
    from typing_extensions import Literal, TypedDict
else:
    from typing import Literal, TypedDict

if typing.TYPE_CHECKING:
    from indexpy.applications import Index
    from indexpy.requests import HttpRequest

from indexpy.exceptions import RequestValidationError
from indexpy.requests import request
from indexpy.responses import HTMLResponse, HttpResponse, JSONResponse
from indexpy.routing import HttpRoute, Routes
from indexpy.utils import F

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
        template_name: Literal["redoc", "swagger", "rapidoc"] = "swagger",
        template: str = "",
    ) -> None:
        if template == "":
            template = (
                Path(__file__).absolute().parent / f"{template_name}.html"
            ).read_text(encoding="utf8")

        self.html_template = template

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
                self.path2tag.setdefault(path, []).append(tag_name)

    def _generate_paths(self, app: Index, definitions: dict) -> Dict[str, Any]:
        generate_path_docs = lambda path_format, handler: (
            path_format,
            self._generate_path(handler, path_format, definitions),
        )
        return dict(
            app.router.http_tree.iterator()
            | F(map, lambda x: generate_path_docs(*x))
            | F(filter, lambda kv: bool(kv[1]))
        )

    def _generate_path(self, view: Any, path: str, definitions: dict) -> Dict[str, Any]:
        """
        Generate documents under a path
        """
        if hasattr(view, "__methods__"):
            generate_method_docs = lambda method: (
                method,
                self._generate_method(
                    getattr(view, method),
                    path,
                    definitions,
                ),
            )
            return dict(
                view.__methods__
                | F(map, lambda method: method.lower())
                | F(filter, lambda method: method != "options")
                | F(map, generate_method_docs)
                | F(filter, lambda method_and_docs: bool(method_and_docs[1]))
            )
        elif hasattr(view, "__method__"):
            return {
                view.__method__.lower(): self._generate_method(view, path, definitions),
            } | F(lambda d: {k: v for k, v in d.items() if v})
        else:
            return {}

    def _generate_method(
        self, func: object, path: str, definitions: dict
    ) -> Dict[str, Any]:
        result: Dict[str, Any] = {}

        doc = func.__doc__
        if isinstance(doc, str):
            result.update(
                zip(
                    ("summary", "description"),
                    doc.strip().split("\n\n", 1) | F(map, lambda i: i.strip()),
                )
            )

        # generate params schema
        parameters = (
            ["path", "query", "header", "cookie"]
            | F(map, lambda key: (getattr(func, "__parameters__", {}).get(key), key))
            | F(map, lambda args: schema_parameter(*args))
            | F(reduce, operator.add)
        )
        result["parameters"] = parameters

        # generate request body schema
        request_body, _definitions = schema_request_body(
            getattr(func, "__request_body__", None)
        )
        result["requestBody"] = request_body
        definitions.update(_definitions)

        # generate responses schema
        __responses__ = getattr(func, "__responses__", {})
        responses: Dict[int, Any] = {}
        if parameters or request_body:
            responses[422] = {
                "content": {
                    "application/json": {"schema": RequestValidationError.schema()}
                },
                "description": "Failed to verify request parameters",
            }

        for status, info in __responses__.items():
            _ = responses[int(status)] = dict(info)
            if _.get("content") is not None:
                _["content"], _definitions = schema_response(_["content"])
                definitions.update(_definitions)

        result["responses"] = responses

        # set path tags
        if result and path in self.path2tag:
            result["tags"] = self.path2tag[path]

        # merge user custom operation info
        return merge_openapi_info(
            result | F(lambda d: {k: v for k, v in d.items() if v}),
            getattr(func, "__extra_docs__", {}),
        )

    def create_docs(self, request: HttpRequest) -> dict:
        openapi: dict = deepcopy(self.openapi)
        definitions: Dict[str, Any] = {}
        openapi["servers"] = [
            {
                "url": f"{request.url.scheme}://{request.url.netloc}",
                "description": "Current server",
            }
        ]
        openapi["paths"] = deepcopy(self._generate_paths(request.app, definitions))
        openapi["definitions"] = deepcopy(definitions)
        return openapi

    @property
    def routes(self) -> Routes:
        async def template() -> HttpResponse:
            return HTMLResponse(self.html_template)

        async def docs() -> HttpResponse:
            openapi = self.create_docs(request)
            return JSONResponse(openapi)

        return Routes(HttpRoute("/", template), HttpRoute("/docs", docs))
