import sys
from types import TracebackType
from typing import Any, Type, Tuple, Union, Callable, Iterable, MutableMapping, Optional

if sys.version_info[:2] < (3, 8):
    from typing_extensions import TypedDict
else:
    from typing import TypedDict

from starlette.types import *

from .http.request import Request
from .http.responses import Response
from .websocket.request import WebSocket

__all__ = (
    "Request",
    "Response",
    "WebSocket",
    "Scope",
    "Message",
    "Receive",
    "Send",
    "ASGIApp",
    "ExcInfo",
    "Environ",
    "StartResponse",
    "WSGIApp",
)

# WSGI: view PEP3333
ExcInfo = Tuple[Type[BaseException], BaseException, Optional[TracebackType]]

Environ = MutableMapping[str, Any]

StartResponse = Callable[[str, Iterable[Tuple[str, str]], Optional[ExcInfo]], None]

WSGIApp = Callable[[Environ, StartResponse], Iterable[Union[str, bytes]]]


class FactoryClass(TypedDict):
    """
    `Index().factory_class` type
    """

    http: typing.Type[Request]
    websocket: typing.Type[WebSocket]
