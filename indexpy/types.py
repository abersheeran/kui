from typing import (
    MutableMapping,
    Any,
    Tuple,
    Union,
    Callable,
    Iterable,
)
from .http.request import Request
from .http.responses import Response
from .websocket.request import WebSocket


# WSGI: view PEP3333
Environ = MutableMapping[str, Any]
StartResponse = Callable[[str, Iterable[Tuple[str, str]]], None]
WSGIApp = Callable[[Environ, StartResponse], Iterable[Union[str, bytes]]]
