from __future__ import annotations

import dataclasses
from typing import Optional

from pydantic.fields import FieldInfo

from indexpy.types import Literal


class PathInfo(FieldInfo):
    pass


class QueryInfo(FieldInfo):
    pass


class HeaderInfo(FieldInfo):
    pass


class CookieInfo(FieldInfo):
    pass


class BodyInfo(FieldInfo):
    pass


@dataclasses.dataclass
class ExclusiveInfo:
    name: Literal["path", "query", "header", "cookie", "body"]
    title: Optional[str] = None
    description: Optional[str] = None
