from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable, Optional

from pydantic.fields import FieldInfo as _FieldInfo
from pydantic.fields import NoArgAnyCallable, Undefined
from typing_extensions import Literal


class FieldInfo(_FieldInfo):
    __slots__ = _FieldInfo.__slots__

    _in: Literal["path", "query", "header", "cookie", "body", "request"]


class PathInfo(FieldInfo):
    __slots__ = ("exclusive", *FieldInfo.__slots__)

    _in: Literal["path"] = "path"

    def __init__(self, default: Any = Undefined, **kwargs: Any) -> None:
        self.exclusive = kwargs.pop("exclusive")
        super().__init__(default, **kwargs)


class QueryInfo(FieldInfo):
    __slots__ = ("exclusive", *FieldInfo.__slots__)

    _in: Literal["query"] = "query"

    def __init__(self, default: Any = Undefined, **kwargs: Any) -> None:
        self.exclusive = kwargs.pop("exclusive")
        super().__init__(default, **kwargs)


class HeaderInfo(FieldInfo):
    __slots__ = ("exclusive", *FieldInfo.__slots__)

    _in: Literal["header"] = "header"

    def __init__(self, default: Any = Undefined, **kwargs: Any) -> None:
        if isinstance(kwargs.get("alias"), str):
            kwargs["alias"] = kwargs["alias"].lower()
        self.exclusive = kwargs.pop("exclusive")
        super().__init__(default, **kwargs)


class CookieInfo(FieldInfo):
    __slots__ = ("exclusive", *FieldInfo.__slots__)

    _in: Literal["cookie"] = "cookie"

    def __init__(self, default: Any = Undefined, **kwargs: Any) -> None:
        self.exclusive = kwargs.pop("exclusive")
        super().__init__(default, **kwargs)


class BodyInfo(FieldInfo):
    __slots__ = ("exclusive", *FieldInfo.__slots__)

    _in: Literal["body"] = "body"

    def __init__(self, default: Any = Undefined, **kwargs: Any) -> None:
        self.exclusive = kwargs.pop("exclusive")
        super().__init__(default, **kwargs)


@dataclass
class RequestAttrInfo:
    __slots__ = ("default", "default_factory", "alias")

    default: Any
    default_factory: Optional[NoArgAnyCallable]
    alias: Optional[str]


@dataclass
class DependInfo:
    __slots__ = ("call", "cache")

    call: Callable
    cache: bool
