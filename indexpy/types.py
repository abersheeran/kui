import sys
from types import TracebackType
from typing import (
    Any,
    Awaitable,
    Callable,
    Iterable,
    MutableMapping,
    Optional,
    Tuple,
    Type,
)

if sys.version_info[:2] < (3, 8):
    from typing_extensions import Final, Literal, TypedDict, final
else:  # pragma: no cover
    from typing import Final, Literal, TypedDict, final

__all__ = [
    # built-in types
    "TypedDict",
    "Literal",
    "Final",
    "final",
]

# ASGI
Scope = MutableMapping[str, Any]

Message = MutableMapping[str, Any]

Receive = Callable[[], Awaitable[Message]]

Send = Callable[[Message], Awaitable[None]]

ASGIApp = Callable[[Scope, Receive, Send], Awaitable[None]]

# WSGI: view PEP3333
ExcInfo = Tuple[Type[BaseException], BaseException, Optional[TracebackType]]

Environ = MutableMapping[str, Any]

StartResponse = Callable[[str, Iterable[Tuple[str, str]], Optional[ExcInfo]], None]

WSGIApp = Callable[[Environ, StartResponse], Iterable[bytes]]

__all__ += [
    "Scope",
    "Message",
    "Receive",
    "Send",
    "ASGIApp",
    "ExcInfo",
    "Environ",
    "StartResponse",
    "WSGIApp",
]

LOWER_HTTP_METHODS = Literal[
    "get", "post", "put", "patch", "delete", "head", "options", "trace"
]

UPPER_HTTP_METHODS = Literal[
    "GET", "POST", "PUT", "PATCH", "DELETE", "HEAD", "OPTIONS", "TRACE"
]

__all__ += ["LOWER_HTTP_METHODS", "UPPER_HTTP_METHODS"]
