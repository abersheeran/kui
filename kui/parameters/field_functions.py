from __future__ import annotations

from typing import Any, Callable, Optional, TypeVar

from pydantic.fields import NoArgAnyCallable, Undefined
from typing_extensions import Literal

from .fields import (
    BodyInfo,
    CookieInfo,
    DependInfo,
    HeaderInfo,
    PathInfo,
    QueryInfo,
    RequestAttrInfo,
)

T = TypeVar("T")


def Path(
    default: Any = Undefined,
    *,
    default_factory: Optional[NoArgAnyCallable] = None,
    alias: str | None = None,
    title: str | None = None,
    description: str | None = None,
    exclusive: bool = False,
    **extra: Any,
) -> Any:
    """
    Used to provide extra information about a field.

    :param default: since this is replacing the field’s default, its first argument is used
      to set the default, use ellipsis (``...``) to indicate the field is required
    :param default_factory: callable that will be called when a default value is needed for this field
      If both `default` and `default_factory` are set, an error is raised.
    :param alias: the public name of the field
    :param title: can be any string, used in the schema
    :param description: can be any string, used in the schema
    :param exclusive: decide whether this field receives all parameters
    :param **extra: any additional keyword arguments will be added as is to the schema
    """
    field_info = PathInfo(
        default,
        default_factory=default_factory,
        alias=alias,
        title=title,
        description=description,
        exclusive=exclusive,
        **extra,
    )
    field_info._validate()
    return field_info


def Query(
    default: Any = Undefined,
    *,
    default_factory: Optional[NoArgAnyCallable] = None,
    alias: str | None = None,
    title: str | None = None,
    description: str | None = None,
    exclusive: bool = False,
    **extra: Any,
) -> Any:
    """
    Used to provide extra information about a field.

    :param default: since this is replacing the field’s default, its first argument is used
      to set the default, use ellipsis (``...``) to indicate the field is required
    :param default_factory: callable that will be called when a default value is needed for this field
      If both `default` and `default_factory` are set, an error is raised.
    :param alias: the public name of the field
    :param title: can be any string, used in the schema
    :param description: can be any string, used in the schema
    :param exclusive: decide whether this field receives all parameters
    :param **extra: any additional keyword arguments will be added as is to the schema
    """
    field_info = QueryInfo(
        default,
        default_factory=default_factory,
        alias=alias,
        title=title,
        description=description,
        exclusive=exclusive,
        **extra,
    )
    field_info._validate()
    return field_info


def Header(
    default: Any = Undefined,
    *,
    default_factory: Optional[NoArgAnyCallable] = None,
    alias: str | None = None,
    title: str | None = None,
    description: str | None = None,
    exclusive: bool = False,
    **extra: Any,
) -> Any:
    """
    Used to provide extra information about a field.

    :param default: since this is replacing the field’s default, its first argument is used
      to set the default, use ellipsis (``...``) to indicate the field is required
    :param default_factory: callable that will be called when a default value is needed for this field
      If both `default` and `default_factory` are set, an error is raised.
    :param alias: the public name of the field
    :param title: can be any string, used in the schema
    :param description: can be any string, used in the schema
    :param exclusive: decide whether this field receives all parameters
    :param **extra: any additional keyword arguments will be added as is to the schema
    """
    field_info = HeaderInfo(
        default,
        default_factory=default_factory,
        alias=alias,
        title=title,
        description=description,
        exclusive=exclusive,
        **extra,
    )
    field_info._validate()
    return field_info


def Cookie(
    default: Any = Undefined,
    *,
    default_factory: Optional[NoArgAnyCallable] = None,
    alias: str | None = None,
    title: str | None = None,
    description: str | None = None,
    exclusive: bool = False,
    **extra: Any,
) -> Any:
    """
    Used to provide extra information about a field.

    :param default: since this is replacing the field’s default, its first argument is used
      to set the default, use ellipsis (``...``) to indicate the field is required
    :param default_factory: callable that will be called when a default value is needed for this field
      If both `default` and `default_factory` are set, an error is raised.
    :param alias: the public name of the field
    :param title: can be any string, used in the schema
    :param description: can be any string, used in the schema
    :param exclusive: decide whether this field receives all parameters
    :param **extra: any additional keyword arguments will be added as is to the schema
    """
    field_info = CookieInfo(
        default,
        default_factory=default_factory,
        alias=alias,
        title=title,
        description=description,
        exclusive=exclusive,
        **extra,
    )
    field_info._validate()
    return field_info


def Body(
    default: Any = Undefined,
    *,
    default_factory: Optional[NoArgAnyCallable] = None,
    alias: str | None = None,
    title: str | None = None,
    description: str | None = None,
    exclusive: bool = False,
    **extra: Any,
) -> Any:
    """
    Used to provide extra information about a field.

    :param default: since this is replacing the field’s default, its first argument is used
      to set the default, use ellipsis (``...``) to indicate the field is required
    :param default_factory: callable that will be called when a default value is needed for this field
      If both `default` and `default_factory` are set, an error is raised.
    :param alias: the public name of the field
    :param title: can be any string, used in the schema
    :param description: can be any string, used in the schema
    :param exclusive: decide whether this field receives all parameters
    :param **extra: any additional keyword arguments will be added as is to the schema
    """
    field_info = BodyInfo(
        default,
        default_factory=default_factory,
        alias=alias,
        title=title,
        description=description,
        exclusive=exclusive,
        **extra,
    )
    field_info._validate()
    return field_info


def RequestAttr(
    default: Any = Undefined,
    *,
    default_factory: Optional[NoArgAnyCallable] = None,
    alias: str | None = None,
) -> Any:
    """
    Used to provide extra information about a field.

    :param default: since this is replacing the field’s default, its first argument is used
      to set the default, use ellipsis (``...``) to indicate the field is required
    :param default_factory: callable that will be called when a default value is needed for this field
      If both `default` and `default_factory` are set, an error is raised.
    :param alias: the public name of the field
    """
    if default is not Undefined and default_factory is not None:
        raise ValueError("cannot specify both default and default_factory")
    return RequestAttrInfo(default, default_factory=default_factory, alias=alias)


def Depends(call: Callable, *, cache=True) -> Any:
    """
    Used to provide extra information about a field.

    :param call: callable that will be called when a dependency is needed for this field
    :param cache: whether to cache the result of the dependency call in the request state
    """
    return DependInfo(call, cache=cache)


def RequiredApiKeyAuth(
    name: str, position: Literal["query", "header", "cookie"] = "header"
) -> Any:
    if position == "query":
        class_ = Query
    elif position == "header":
        class_ = Header
    elif position == "cookie":
        class_ = Cookie
    else:
        raise ValueError(
            f"Invalid position {position}, must be one of ('query', 'header', 'cookie')"
        )

    return class_(
        alias=name,
        title="API Key",
        security={
            "scheme": {"ApiKeyAuth": {"type": "apiKey", "name": name, "in": position}},
            "required": {"ApiKeyAuth": []},
        },
    )


def RequiredBearerAuth() -> Any:
    return Header(
        alias="authorization",
        title="Bearer Auth",
        security={
            "scheme": {"BearerAuth": {"type": "http", "scheme": "bearer"}},
            "required": {"BearerAuth": []},
        },
    )


def RequiredBasicAuth() -> Any:
    return Header(
        alias="authorization",
        title="Basic Auth",
        security={
            "scheme": {"BasicAuth": {"type": "http", "scheme": "basic"}},
            "required": {"BasicAuth": []},
        },
    )
