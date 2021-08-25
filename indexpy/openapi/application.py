from __future__ import annotations

import asyncio
import copy
import inspect
import json
import operator
import typing
from functools import reduce
from hashlib import md5
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Sequence, Tuple, TypeVar

from typing_extensions import Literal, TypedDict

if typing.TYPE_CHECKING:
    from ..applications import Index
    from ..requests import HttpRequest

from ..exceptions import RequestValidationError
from ..requests import request
from ..responses import HTMLResponse, JSONResponse
from ..routing import HttpRoute, Routes
from . import specification as spec
from .extra_docs import merge_openapi_info
from .schema import schema_parameter, schema_request_body, schema_response

TagDetail = TypedDict("TagDetail", {"description": str, "paths": Sequence[str]})


class OpenAPI:
    def __init__(
        self,
        info: spec.Info = {"title": "IndexPy API", "version": "1.0.0"},
        security_schemes: Dict[str, spec.SecurityScheme | spec.Reference] = {},
        *,
        tags: Dict[str, TagDetail] = {},
        template_name: Literal["redoc", "swagger", "rapidoc"] = "swagger",
        template: str = "",
    ) -> None:
        if template == "":
            template = (
                Path(__file__).absolute().parent / "templates" / f"{template_name}.html"
            ).read_text(encoding="utf8")

        self.html_template = template

        self.openapi: spec.OpenAPI = {
            "openapi": "3.0.3",
            "info": info,
            "paths": {},
            "tags": [
                {"name": tag_name, "description": tag_info.get("description", "")}
                for tag_name, tag_info in tags.items()
            ],
            "components": {
                "schemas": {"RequestValidationError": RequestValidationError.schema()},
            },
        }
        if security_schemes:
            self.openapi["components"]["securitySchemes"] = security_schemes
        self.path2tag: Dict[str, List[str]] = {}
        for tag_name, tag_info in tags.items():
            for path in tag_info["paths"]:
                self.path2tag.setdefault(path, []).append(tag_name)
        self.definitions: dict = {}

    def _generate_paths(self, app: Index) -> Tuple[spec.Paths, dict]:
        _definitions: dict = {}
        update_definitions = lambda path_item, x: _definitions.update(x) or path_item
        return {
            path: openapi_path_item
            for path, openapi_path_item in (
                (
                    path_format,
                    update_definitions(*self._generate_path(handler, path_format)),
                )
                for path_format, handler in app.router.http_tree.iterator()
            )
            if openapi_path_item
        }, _definitions

    def _generate_path(self, view: Any, path: str) -> Tuple[spec.PathItem, dict]:
        """
        Generate documents under a path
        """
        _definitions: dict = {}
        update_definitions = lambda path_item, x: _definitions.update(x) or path_item
        if hasattr(view, "__methods__"):
            result = clear_empty(
                {
                    method: update_definitions(
                        *self._generate_method(getattr(view, method), path)
                    )
                    for method in (
                        method.lower()
                        for method in typing.cast(Iterable[str], view.__methods__)
                        if method.lower() != "options"
                    )
                }
            )
        elif hasattr(view, "__method__"):
            result = clear_empty(
                {
                    typing.cast(str, view.__method__).lower(): update_definitions(
                        *self._generate_method(view, path)
                    ),
                }
            )
        else:
            result = {}

        return typing.cast(spec.PathItem, result), _definitions

    def _generate_method(self, func: Any, path: str) -> Tuple[spec.Operation, dict]:
        result: Dict[str, Any] = {}
        _definitions: dict = {}
        update_definitions = lambda path_item, x: _definitions.update(x) or path_item

        # This is mypy check error, if you use pyright/pylance, this is all fine.
        if hasattr(func, "__summary__") and isinstance(func.__summary__, str):  # type: ignore
            result["summary"] = func.__summary__  # type: ignore
        if hasattr(func, "__description__") and isinstance(func.__description__, str):  # type: ignore
            result["description"] = func.__description__  # type: ignore

        if isinstance(func.__doc__, str):
            clean_doc = inspect.cleandoc(func.__doc__)
            if "summary" not in result and "description" not in result:
                result.update(
                    zip(("summary", "description"), clean_doc.split("\n\n", 1))
                )
            elif "description" not in result:
                result["description"] = clean_doc
            else:
                result["summary"] = ""

        # generate params schema
        parameters = reduce(
            operator.add,
            map(
                lambda key: schema_parameter(
                    create_model(getattr(func, "__docs_parameters__", {}).get(key, [])),
                    typing.cast(Literal["path", "query", "header", "cookie"], key),
                ),
                ["path", "query", "header", "cookie"],
            ),
        )
        result["parameters"] = parameters

        # generate request body schema
        request_body = update_definitions(
            *schema_request_body(
                create_model(getattr(func, "__docs_request_body__", []))
            )
        )
        result["requestBody"] = request_body

        # generate responses schema
        responses: spec.Responses = {}
        if parameters or request_body:
            responses["422"] = {
                "content": {
                    "application/json": {
                        "schema": {
                            "$ref": "#/components/schemas/RequestValidationError"
                        }
                    }
                },
                "description": "Failed to verify request parameters",
            }
        for status, info in getattr(func, "__docs_responses__", {}).items():
            _ = responses[status] = copy.copy(info)
            if _.get("content") is not None:
                _["content"] = update_definitions(*schema_response(_["content"]))

        result["responses"] = responses

        # set path tags
        if result and path in self.path2tag:
            result["tags"] = self.path2tag[path]

        result["tags"] = getattr(func, "__tags__", []) + result.get("tags", [])

        # merge user custom operation info
        return (
            typing.cast(
                spec.Operation,
                merge_openapi_info(
                    clear_empty(result), getattr(func, "__docs_extra__", {})
                ),
            ),
            _definitions,
        )

    def create_docs(self, request: HttpRequest) -> spec.OpenAPI:
        openapi = copy.deepcopy(self.openapi)
        openapi["servers"] = [
            {
                "url": f"{request.url.scheme}://{request.url.netloc}",
                "description": "Current server",
            }
        ]
        openapi["paths"], definitions = copy.deepcopy(self._generate_paths(request.app))
        for path_item in openapi["paths"].values():
            for operation in filter(lambda x: isinstance(x, dict), path_item.values()):
                operation = typing.cast(spec.Operation, operation)
                if "responses" not in operation:
                    operation["responses"] = {}
        openapi["components"].setdefault("schemas", {}).update(definitions)
        return openapi

    @property
    def routes(self) -> Routes:
        async def redirect():
            return request.url.replace(path=request.url.path + "/")

        async def template():
            return HTMLResponse(self.html_template)

        async def json_docs():
            openapi = self.create_docs(request)
            return JSONResponse(
                openapi, headers={"hash": md5(json.dumps(openapi).encode()).hexdigest()}
            )

        async def heartbeat():
            async def g():
                openapi = self.create_docs(request)
                yield {
                    "id": md5(json.dumps(openapi).encode()).hexdigest(),
                    "data": json.dumps(openapi),
                }
                while not request.app.should_exit:
                    await asyncio.sleep(1)

            return g()

        return Routes(
            HttpRoute("", redirect),
            HttpRoute("/", template),
            HttpRoute("/json", json_docs),
            HttpRoute("/heartbeat", heartbeat),
        )


T_Dict = TypeVar("T_Dict", bound=Dict)


def clear_empty(d: T_Dict) -> T_Dict:
    return typing.cast(T_Dict, {k: v for k, v in d.items() if v})


def create_model(bases: List[type]) -> Optional[type]:
    if bases:
        return type("T_SchemaModel", tuple(bases), {})
    else:
        return None
