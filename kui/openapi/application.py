from __future__ import annotations

import copy
import inspect
import operator
import typing
from functools import reduce
from pathlib import Path
from typing import (
    TYPE_CHECKING,
    Any,
    Dict,
    Iterable,
    List,
    Optional,
    Sequence,
    Tuple,
    TypeVar,
)

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
            self.openapi.get("components", {})["securitySchemes"] = security_schemes
        self.path2tag: Dict[str, List[str]] = {}
        for tag_name, tag_info in tags.items():
            for path in tag_info.get("paths", []):
                self.path2tag.setdefault(path, []).append(tag_name)
        self.definitions: dict = {}

    def _generate_paths(
        self, application: ASGIKui | WSGIKui
    ) -> Tuple[spec.Paths, dict]:
        _definitions: dict = {}
        update_definitions = lambda path_item, x: _definitions.update(x) or path_item
        return {
            path: openapi_path_item
            for path, openapi_path_item in (
                (
                    path_format,
                    update_definitions(
                        *self._generate_path(application, handler, path_format)
                    ),
                )
                for path_format, handler in application.router.http_tree.iterator()
            )
            if openapi_path_item
        }, _definitions

    def _generate_path(
        self, application: ASGIKui | WSGIKui, view: Any, path: str
    ) -> Tuple[spec.PathItem, dict]:
        """
        Generate documents under a path
        """
        _definitions: dict = {}
        update_definitions = lambda path_item, x: _definitions.update(x) or path_item
        if hasattr(view, "__methods__"):
            result = clear_empty(
                {
                    method: update_definitions(
                        *self._generate_method(application, getattr(view, method), path)
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
                        *self._generate_method(application, view, path)
                    ),
                }
            )
        else:
            result = {}

        return typing.cast(spec.PathItem, result), _definitions

    def _generate_method(
        self, application: ASGIKui | WSGIKui, func: Any, path: str
    ) -> Tuple[spec.Operation, dict]:
        result: Dict[str, Any] = {}
        _definitions: dict = {}
        update_definitions = lambda path_item, x: _definitions.update(x) or path_item

        # This is mypy check error, if you use pyright/pylance, this is all fine.
        if hasattr(func, "__docs_summary__") and isinstance(func.__docs_summary__, str):  # type: ignore
            result["summary"] = func.__docs_summary__  # type: ignore
        if hasattr(func, "__docs_description__") and isinstance(func.__docs_description__, str):  # type: ignore
            result["description"] = func.__docs_description__  # type: ignore

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
                create_model(getattr(func, "__docs_request_body__", [])), application
            )
        )
        result["requestBody"] = request_body

        # generate responses schema
        responses: spec.Responses = {}
        if parameters or request_body:
            handler = application.exception_middleware.lookup_handler(
                RequestValidationError(ValidationError([], BaseModel), "body")
            )
            if handler is None:
                raise RuntimeError
            for status, info in _get_response_docs(handler).items():
                _ = responses[status] = copy.copy(info)
                if _.get("content") is not None:
                    _["content"] = update_definitions(*schema_response(_["content"]))
        for status, info in getattr(func, "__docs_responses__", {}).items():
            _ = responses[status] = copy.copy(info)
            if _.get("content") is not None:
                _["content"] = update_definitions(*schema_response(_["content"]))

        result["responses"] = responses

        # set path tags
        if result and path in self.path2tag:
            result["tags"] = self.path2tag[path]

        result["tags"] = getattr(func, "__docs_tags__", []) + result.get("tags", [])

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
        openapi["paths"], definitions = copy.deepcopy(self._generate_paths(request.app))
        for path_item in openapi["paths"].values():
            for operation in filter(lambda x: isinstance(x, dict), path_item.values()):
                operation = typing.cast(spec.Operation, operation)
                if "responses" not in operation:
                    operation["responses"] = {}
        openapi.get("components", {}).setdefault("schemas", {}).update(definitions)
        return openapi


T_Dict = TypeVar("T_Dict", bound=Dict)


def clear_empty(d: T_Dict) -> T_Dict:
    return typing.cast(T_Dict, {k: v for k, v in d.items() if v})


def create_model(bases: List[type]) -> Optional[type]:
    if bases:
        return type("T_SchemaModel", tuple(bases), {})
    else:
        return None
