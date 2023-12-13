from __future__ import annotations

from typing import Any, Callable, Optional, TypeVar

from pydantic import Field
from typing_extensions import Annotated

from ..pydantic_compatible import Undefined
from .fields import Depends as DependInfo
from .fields import InBody, InCookie, InHeader, InPath, InQuery

T = TypeVar("T")


def Path(
    default: Any = Undefined,
    *,
    default_factory: Optional[Callable[[], None]] = None,
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
    :param **extra: any pydantic field kwargs
    """
    field_info = Field(
        default,
        default_factory=default_factory,
        alias=alias,
        title=title,
        description=description,
        **extra,
    )
    return Annotated[Any, field_info, InPath(exclusive=exclusive)]


def Query(
    default: Any = Undefined,
    *,
    default_factory: Optional[Callable[[], None]] = None,
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
    :param **extra: any pydantic field kwargs
    """
    field_info = Field(
        default,
        default_factory=default_factory,
        alias=alias,
        title=title,
        description=description,
        **extra,
    )
    return Annotated[Any, field_info, InQuery(exclusive=exclusive)]


def Header(
    default: Any = Undefined,
    *,
    default_factory: Optional[Callable[[], None]] = None,
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
    :param **extra: any pydantic field kwargs
    """
    field_info = Field(
        default,
        default_factory=default_factory,
        alias=alias.lower() if alias else None,
        title=title,
        description=description,
        **extra,
    )
    return Annotated[Any, field_info, InHeader(exclusive=exclusive)]


def Cookie(
    default: Any = Undefined,
    *,
    default_factory: Optional[Callable[[], None]] = None,
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
    :param **extra: any pydantic field kwargs
    """
    field_info = Field(
        default,
        default_factory=default_factory,
        alias=alias,
        title=title,
        description=description,
        **extra,
    )
    return Annotated[Any, field_info, InCookie(exclusive=exclusive)]


def Body(
    default: Any = Undefined,
    *,
    default_factory: Optional[Callable[[], None]] = None,
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
    :param **extra: any pydantic field kwargs
    """
    field_info = Field(
        default,
        default_factory=default_factory,
        alias=alias,
        title=title,
        description=description,
        **extra,
    )
    return Annotated[Any, field_info, InBody(exclusive=exclusive)]


def Depends(call: Callable, *, cache=True) -> Any:
    """
    Used to provide extra information about a field.

    :param call: callable that will be called when a dependency is needed for this field
    :param cache: whether to cache the result of the dependency call in the request state
    """
    return DependInfo(call, cache=cache)
