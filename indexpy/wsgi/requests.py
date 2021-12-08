from __future__ import annotations

import typing
from contextvars import ContextVar
from http import HTTPStatus

from baize.datastructures import ContentType
from baize.exceptions import HTTPException
from baize.utils import cached_property
from baize.wsgi import HTTPConnection as BaiZeHTTPConnection
from baize.wsgi import Request as BaiZeRequest
from typing_extensions import Annotated

if typing.TYPE_CHECKING:
    from .applications import HintAPI

from .utils import State, bind_contextvar


class HTTPConnection(BaiZeHTTPConnection, typing.MutableMapping[str, typing.Any]):
    def __setitem__(self, name: str, value: typing.Any) -> None:
        self._environ[name] = value

    def __delitem__(self, name: str) -> None:
        del self._environ[name]

    @cached_property
    def state(self) -> State:
        self._environ.setdefault("state", {})
        return State(self._environ["state"])

    @cached_property
    def app(self) -> HintAPI:
        return self["app"]  # type: ignore


class HttpRequest(BaiZeRequest, HTTPConnection):
    def data(
        self,
    ) -> Annotated[
        typing.Any,
        ContentType("application/json"),
        ContentType("application/x-www-form-urlencoded"),
        ContentType("multipart/form-data"),
    ]:
        content_type = self.content_type
        if content_type == "application/json":
            return self.json
        elif content_type in (
            "multipart/form-data",
            "application/x-www-form-urlencoded",
        ):
            return self.form

        raise HTTPException(HTTPStatus.UNSUPPORTED_MEDIA_TYPE)


request_var: ContextVar[HttpRequest] = ContextVar("request")

request = bind_contextvar(request_var)
