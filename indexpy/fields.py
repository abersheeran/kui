from __future__ import annotations

import sys
from dataclasses import dataclass
from typing import Any

if sys.version_info[:2] < (3, 8):
    from typing_extensions import Literal
else:
    from typing import Literal

from pydantic.fields import FieldInfo as _FieldInfo
from pydantic.fields import Undefined


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
class RequestInfo:
    __slots__ = ("alias",)

    alias: str
