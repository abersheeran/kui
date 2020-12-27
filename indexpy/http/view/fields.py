from indexpy.types import Literal

from pydantic.fields import FieldInfo


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


class ExclusiveInfo:
    __slots__ = ("name",)

    def __init__(self, name: Literal["path", "query", "header", "cookie", "body"]):
        self.name = name
