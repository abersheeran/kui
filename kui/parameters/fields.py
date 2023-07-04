from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable

from typing_extensions import Literal

__all__ = [
    "BaseHTTPFieldInfo",
    "InPath",
    "InQuery",
    "InHeader",
    "InCookie",
    "InBody",
    "Depends",
]


@dataclass
class BaseHTTPFieldInfo:
    _in: Literal["path", "query", "header", "cookie", "body"]
    exclusive: bool = False


@dataclass
class InPath(BaseHTTPFieldInfo):
    _in: Literal["path"] = "path"


@dataclass
class InQuery(BaseHTTPFieldInfo):
    _in: Literal["query"] = "query"
    security: Any = None


@dataclass
class InHeader(BaseHTTPFieldInfo):
    _in: Literal["header"] = "header"
    security: Any = None


@dataclass
class InCookie(BaseHTTPFieldInfo):
    _in: Literal["cookie"] = "cookie"
    security: Any = None


@dataclass
class InBody(BaseHTTPFieldInfo):
    _in: Literal["body"] = "body"


@dataclass
class Depends:
    call: Callable
    cache: bool = True
