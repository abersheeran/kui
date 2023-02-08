from __future__ import annotations

import copy
import inspect
import operator
import typing
from functools import reduce
from pathlib import Path
from typing import TYPE_CHECKING, Any, Dict, Iterable, List, Optional, Sequence, TypeVar

from pydantic import BaseModel, ValidationError
from typing_extensions import Literal, TypedDict

if TYPE_CHECKING:
    from ..asgi import Kui as ASGIKui, HttpRequest as ASGIHttpRequest
    from ..wsgi import Kui as WSGIKui, HttpRequest as WSGIHttpRequest

from ..exceptions import RequestValidationError
from ..parameters import _get_response_docs
from . import specification as spec
from .extra_docs import merge_openapi_info
from .schema import schema_parameter, schema_request_body, schema_response


class TagDetailOptional(TypedDict, total=False):
    paths: Sequence[str]


class TagDetail(TagDetailOptional):
    description: str


class OpenAPI:
    def __init__(
        self,
        info: spec.Info = {"title": "Kuí API", "version": "1.0.0"},
        security_schemes: Dict[str, spec.SecurityScheme | spec.Reference] = {},
        *,
        tags: Dict[str, TagDetail] = {},
        template_name: Literal["redoc", "swagger", "rapidoc"] = "swagger",
        template: str = "",
        reload: bool = True,
    ) -> None:
        if template == "":
            template = (
                Path(__file__).absolute().parent / "templates" / f"{template_name}.html"
            ).read_text(encoding="utf8")

        self.html_template = template
        self.reload = reload

        self.openapi = spec.OpenAPI(
            openapi="3.0.3",
            info=info,
            paths={},
            tags=[
                {"name": tag_name, "description": tag_info.get("description", "")}
                for tag_name, tag_info in tags.items()
            ],
            components={},
        )
        if security_schemes:
            components = self.openapi.setdefault("components", {})
            components["securitySchemes"] = security_schemes

        self.path2tag: Dict[str, List[str]] = {}
        for tag_name, tag_info in tags.items():
            for path in tag_info.get("paths", []):
                self.path2tag.setdefault(path, []).append(tag_name)

    def _generate_paths(self, application: ASGIKui | WSGIKui) -> spec.Paths:
        return {
            path: openapi_path_item
            for path, openapi_path_item in (
                (path_format, self._generate_path(application, handler, path_format))
                for path_format, handler in application.router.http_tree.iterator()
            )
            if openapi_path_item
        }

    def _generate_path(
        self, application: ASGIKui | WSGIKui, view: Any, path: str
    ) -> spec.PathItem:
        """
        Generate documents under a path
        """
        if hasattr(view, "__methods__"):
            result = _clear_empty(
                {
                    method: self._generate_method(
                        application, getattr(view, method), path
                    )
                    for method in (
                        method.lower()
                        for method in typing.cast(Iterable[str], view.__methods__)
                        if method.lower() != "options"
                    )
                }
            )
        elif hasattr(view, "__method__"):
            result = _clear_empty(
                {
                    typing.cast(str, view.__method__).lower(): self._generate_method(
                        application, view, path
                    )
                }
            )
        else:
            result = {}

        return typing.cast(spec.PathItem, result)

    def _generate_method(
        self, application: ASGIKui | WSGIKui, func: Any, path: str
    ) -> spec.Operation:
        result: Dict[str, Any] = {}

        # generate summary and description
        if hasattr(func, "__docs_summary__") and isinstance(func.__docs_summary__, str):
            result["summary"] = func.__docs_summary__
        if hasattr(func, "__docs_description__") and isinstance(
            func.__docs_description__, str
        ):
            result["description"] = func.__docs_description__

        if isinstance(func.__doc__, str):
            clean_doc = inspect.cleandoc(func.__doc__)
            if "summary" not in result and "description" not in result:
                result.update(
                    zip(("summary", "description"), clean_doc.split("\n\n", 1))
                )
            elif "description" not in result:
                result["description"] = clean_doc

        # generate params schema
        parameters = reduce(
            operator.add,
            map(
                lambda key: schema_parameter(
                    _create_model(
                        getattr(func, "__docs_parameters__", {}).get(key, [])
                    ),
                    typing.cast(Literal["path", "query", "header", "cookie"], key),
                ),
                ["path", "query", "header", "cookie"],
            ),
        )
        result["parameters"] = parameters

        # generate request body schema
        request_body = schema_request_body(
            _create_model(getattr(func, "__docs_request_body__", [])), application
        )

        result["requestBody"] = request_body

        # generate responses schema
        responses: spec.Responses = {}
        __docs_responses__: List[spec.Responses] = getattr(
            func, "__docs_responses__", []
        )
        if parameters or request_body:
            handler = application.exception_middleware.lookup_handler(
                RequestValidationError(ValidationError([], BaseModel), "body")
            )
            if handler is None:
                raise RuntimeError
            __docs_responses__.extend(_get_response_docs(handler))

        for response_docs in __docs_responses__:
            for response in response_docs.values():
                for media_type, media_type_value in list(
                    response.get("content", {}).items()
                ):
                    schema = schema_response(media_type_value["schema"])  # type: ignore
                    response.get("content", {})[media_type]["schema"] = schema

            need_merge_status_codes = set(responses.keys()) & set(response_docs.keys())
            if need_merge_status_codes:
                for status_code in need_merge_status_codes:
                    content = {
                        **responses[status_code].get("content", {}),
                        **response_docs[status_code].get("content", {}),
                    }
                    if content:
                        responses[status_code]["content"] = content
            else:
                responses.update(response_docs)

        result["responses"] = responses

        # set path tags
        if result and path in self.path2tag:
            result["tags"] = self.path2tag[path]

        result["tags"] = getattr(func, "__docs_tags__", []) + result.get("tags", [])

        # merge user custom operation info
        operation = typing.cast(
            spec.Operation,
            merge_openapi_info(
                _clear_empty(result), getattr(func, "__docs_extra__", {})
            ),
        )
        return operation

    def create_docs(self, request: ASGIHttpRequest | WSGIHttpRequest) -> spec.OpenAPI:
        openapi = copy.deepcopy(self.openapi)
        openapi["servers"] = [
            {
                "url": "/",
                "description": "Current server",
            },
            spec.Server(
                url="{scheme}://{address}/",
                description="Custom API Server Host",
                variables={
                    "scheme": {
                        "default": request.url.scheme,
                        "enum": ["http", "https"],
                        "description": "http or https",
                    },
                    "address": {
                        "default": request.url.netloc,
                        "description": "api server's host[:port]",
                    },
                },
            ),
        ]
        paths = copy.deepcopy(self._generate_paths(request.app))
        for path_item in paths.values():
            for operation in filter(lambda x: isinstance(x, dict), path_item.values()):
                operation = typing.cast(spec.Operation, operation)
                if "responses" not in operation:
                    operation["responses"] = {}
        components = openapi.setdefault("components", {})
        schemas = components.setdefault("schemas", {})
        schemas.update(**_pop_definitions(paths))
        openapi["paths"] = paths
        return openapi


_DictType = TypeVar("_DictType", bound=Dict)


def _clear_empty(d: _DictType) -> _DictType:
    return typing.cast(_DictType, {k: v for k, v in d.items() if v})


def _create_model(bases: List[type]) -> Optional[type]:
    if bases:
        return type("T_SchemaModel", tuple(bases), {})
    else:
        return None


def _pop_definitions(d: Dict[str, Any]) -> Dict[str, spec.Schema]:
    definitions: Dict[str, Any] = {}
    for key, value in d.items():
        if key == "schema":
            return value.pop("definitions", {})

        if isinstance(value, dict):
            definitions.update(_pop_definitions(value))
        elif isinstance(value, (list, tuple)):
            for v in value:
                definitions.update(_pop_definitions(v))
        else:
            pass
    return definitions
