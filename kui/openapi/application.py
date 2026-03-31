from __future__ import annotations

import copy
import re
import typing
from pathlib import Path
from typing import (
    TYPE_CHECKING,
    Any,
    Dict,
    Iterable,
    List,
    Optional,
    Sequence,
    Set,
    Tuple,
    TypeVar,
)

from typing_extensions import Literal, TypedDict

if TYPE_CHECKING:
    from ..asgi import HttpRequest as ASGIHttpRequest
    from ..asgi import Kui as ASGIKui
    from ..wsgi import HttpRequest as WSGIHttpRequest
    from ..wsgi import Kui as WSGIKui

from ..exceptions import RequestValidationError
from ..parameters import _get_response_docs
from ..pydantic_compatible import DEFINITIONS_KEY, REF_TEMPLATE
from . import specification as spec
from .extra_docs import merge_openapi_info
from .schema import schema_request_body, schema_response


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
            openapi="3.1.0",
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

        self.security_schemes: Dict[str, spec.SecurityScheme | spec.Reference] = {}

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

        # generate security
        security_set = {}
        for security_dict in getattr(func, "__docs_security__", []):
            self.security_schemes.update(copy.deepcopy(security_dict["scheme"]))
            security_set.update(copy.deepcopy(security_dict["required"]))
        result["security"] = [{k: v} for k, v in security_set.items()]

        # generate params schema
        result["parameters"] = parameters = getattr(func, "__docs_parameters__", [])

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
            handler = application.exception_middleware._lookup_exception_handler(
                RequestValidationError
            )
            if handler is None:
                raise RuntimeError
            __docs_responses__.extend(_get_response_docs(handler))

        for response_docs in __docs_responses__:
            for k, v in list(response_docs.items()):
                del response_docs[k]
                response_docs[str(k)] = v

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
        self.security_schemes = {}
        paths = copy.deepcopy(self._generate_paths(request.app))
        for path_item in paths.values():
            for operation in filter(lambda x: isinstance(x, dict), path_item.values()):
                operation = typing.cast(spec.Operation, operation)
                if "responses" not in operation:
                    operation["responses"] = {}
        components = openapi.setdefault("components", {})
        if self.security_schemes:
            components.setdefault("securitySchemes", {}).update(self.security_schemes)
        schemas = components.setdefault("schemas", {})
        schemas.update(**_resolve_definitions(paths))
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
    # Recursively extract all $defs/definitions blocks from a nested OpenAPI structure.
    definitions: Dict[str, Any] = {}
    for key, value in d.items():
        if key == "schema":
            return value.pop(DEFINITIONS_KEY, {})

        if isinstance(value, dict):
            definitions.update(_pop_definitions(value))
        elif isinstance(value, (list, tuple)):
            for v in value:
                if isinstance(v, dict):
                    definitions.update(_pop_definitions(v))
    return definitions


_REF_PREFIX = REF_TEMPLATE.format(model="")


def _path_to_prefix(path: str) -> str:
    # Convert a path into a readable prefix, for example "/api/v1/users/{id}" -> "ApiV1UsersId".
    parts = re.findall(r"[A-Za-z0-9]+", path)
    if not parts:
        return "Root"
    return "".join(part[:1].upper() + part[1:] for part in parts)


def _update_refs(d: Any, rename_map: Dict[str, str]) -> None:
    # Recursively walk dict/list structures and rewrite $ref strings using rename_map.
    if isinstance(d, dict):
        ref = d.get("$ref")
        if isinstance(ref, str) and ref.startswith(_REF_PREFIX):
            schema_name = ref[len(_REF_PREFIX) :]
            if schema_name in rename_map:
                d["$ref"] = f"{_REF_PREFIX}{rename_map[schema_name]}"
        for value in d.values():
            _update_refs(value, rename_map)
    elif isinstance(d, (list, tuple)):
        for value in d:
            _update_refs(value, rename_map)


def _collect_ref_names(d: Any) -> Set[str]:
    # Recursively collect schema names referenced as "#/components/schemas/X".
    names: Set[str] = set()
    if isinstance(d, dict):
        ref = d.get("$ref")
        if isinstance(ref, str) and ref.startswith(_REF_PREFIX):
            names.add(ref[len(_REF_PREFIX) :])
        for value in d.values():
            names.update(_collect_ref_names(value))
    elif isinstance(d, (list, tuple)):
        for value in d:
            names.update(_collect_ref_names(value))
    return names


def _resolve_definitions(paths: Dict[str, Any]) -> Dict[str, spec.Schema]:
    """
    Extract all schema definitions from paths into components/schemas
    and resolve conflicts between schemas with the same name.

    Algorithm:
    1. Extract each path's $defs.
    2. Detect schemas with the same name but different content (direct conflicts).
    3. Propagate transitive conflicts so schemas that reference conflicting schemas also conflict.
    4. Group conflicting schemas by content so each group shares one path-prefixed name.
    5. Update all $ref references.

    Keep original names when there is no conflict.
    """
    definitions_by_path: Dict[str, Dict[str, spec.Schema]] = {}
    definitions_by_name: Dict[str, List[Tuple[str, spec.Schema]]] = {}

    # Step 1: Extract definitions by path.
    for path, path_item in paths.items():
        path_definitions = _pop_definitions(path_item)
        definitions_by_path[path] = path_definitions
        for schema_name, schema in path_definitions.items():
            definitions_by_name.setdefault(schema_name, []).append((path, schema))

    conflicting_names: Set[str] = set()
    # Step 2: Detect direct conflicts where schemas share a name but differ in content.
    for schema_name, entries in definitions_by_name.items():
        first_schema = entries[0][1]
        if not all(schema == first_schema for _, schema in entries[1:]):
            conflicting_names.add(schema_name)

    changed = True
    # Step 3: Propagate transitive conflicts to schemas that reference conflicting schemas.
    while changed:
        changed = False
        for schema_name, entries in definitions_by_name.items():
            if schema_name in conflicting_names:
                continue
            if _collect_ref_names(entries[0][1]) & conflicting_names:
                conflicting_names.add(schema_name)
                changed = True

    if not conflicting_names:
        # Merge all definitions directly when there are no conflicts.
        result: Dict[str, spec.Schema] = {}
        for defs in definitions_by_path.values():
            result.update(defs)
        return result

    rename_maps: Dict[str, Dict[str, str]] = {path: {} for path in paths}
    final_schemas: Dict[str, spec.Schema] = {}
    used_names = {
        schema_name
        for schema_name in definitions_by_name
        if schema_name not in conflicting_names
    }

    conflict_groups: Dict[str, Dict[str, int]] = {}

    # Compute the grouping key for a schema: compare both its content and the group of any conflicting schemas it references.
    # This keeps schemas with the same content but references to different conflict groups in separate groups.
    def _schema_group_key(
        schema: Any, path: str, groups: Dict[str, Dict[str, int]]
    ) -> Any:
        if isinstance(schema, dict):
            items: List[Tuple[str, Any] | Tuple[str, str, int]] = []
            for key, value in sorted(schema.items()):
                if (
                    key == "$ref"
                    and isinstance(value, str)
                    and value.startswith(_REF_PREFIX)
                ):
                    ref_name = value[len(_REF_PREFIX) :]
                    if ref_name in conflicting_names and path in groups.get(
                        ref_name, {}
                    ):
                        items.append((key, ("$ref", ref_name, groups[ref_name][path])))
                    else:
                        items.append((key, ("$ref", ref_name)))
                else:
                    items.append((key, _schema_group_key(value, path, groups)))
            return tuple(items)
        if isinstance(schema, (list, tuple)):
            return tuple(_schema_group_key(value, path, groups) for value in schema)
        return schema

    # Step 4: Group conflicting schemas by content and reference chain.
    for schema_name in conflicting_names:
        key_to_group: Dict[Any, int] = {}
        for path, schema in definitions_by_name[schema_name]:
            key = _schema_group_key(schema, path, {})
            conflict_groups.setdefault(schema_name, {})[path] = key_to_group.setdefault(
                key, len(key_to_group)
            )

    changed = True
    # Iteratively refine groups until they stabilize.
    while changed:
        changed = False
        next_groups: Dict[str, Dict[str, int]] = {}
        for schema_name in conflicting_names:
            key_to_group = {}
            next_groups[schema_name] = {}
            for path, schema in definitions_by_name[schema_name]:
                key = _schema_group_key(schema, path, conflict_groups)
                next_groups[schema_name][path] = key_to_group.setdefault(
                    key, len(key_to_group)
                )
            if next_groups[schema_name] != conflict_groups[schema_name]:
                changed = True
        conflict_groups = next_groups

    # Step 5: Assign path-prefixed names to conflicting schemas.
    for schema_name, entries in definitions_by_name.items():
        if schema_name not in conflicting_names:
            final_schemas[schema_name] = entries[0][1]
            continue

        grouped_entries: List[Tuple[int, spec.Schema, List[str]]] = []
        for path, schema in entries:
            group_id = conflict_groups[schema_name][path]
            for grouped_id, _, grouped_paths in grouped_entries:
                if group_id == grouped_id:
                    grouped_paths.append(path)
                    break
            else:
                grouped_entries.append((group_id, schema, [path]))

        for _, schema, grouped_paths in grouped_entries:
            prefix = _path_to_prefix(grouped_paths[0])
            resolved_name = f"{prefix}_{schema_name}"
            if resolved_name in used_names:
                suffix = 2
                while f"{resolved_name}_{suffix}" in used_names:
                    suffix += 1
                resolved_name = f"{resolved_name}_{suffix}"
            for path in grouped_paths:
                rename_maps[path][schema_name] = resolved_name
            final_schemas[resolved_name] = schema
            used_names.add(resolved_name)

    # Step 6: Update $ref values in paths and definitions.
    for path, path_item in paths.items():
        rename_map = rename_maps[path]
        if not rename_map:
            continue

        _update_refs(path_item, rename_map)
        for schema in definitions_by_path[path].values():
            _update_refs(schema, rename_map)

    return final_schemas
