from __future__ import annotations

from typing import Any, Optional

from pydantic.fields import NoArgAnyCallable, Undefined

from .fields import BodyInfo, CookieInfo, HeaderInfo, PathInfo, QueryInfo, RequestInfo

__all__ = ["Path", "Query", "Header", "Cookie", "Body", "Request"]


def Path(
    default: Any = Undefined,
    *,
    default_factory: Optional[NoArgAnyCallable] = None,
    alias: str = None,
    title: str = None,
    description: str = None,
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
    alias: str = None,
    title: str = None,
    description: str = None,
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
    alias: str = None,
    title: str = None,
    description: str = None,
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
    alias: str = None,
    title: str = None,
    description: str = None,
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
    alias: str = None,
    title: str = None,
    description: str = None,
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


def Request(alias: str = None) -> Any:
    """
    Used to provide extra information about a field.

    :param alias: the public name of the field
    """
    return RequestInfo(alias or "")
