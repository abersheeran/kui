from typing import (
    MutableMapping,
    Any,
    Tuple,
    Union,
    Awaitable,
    Callable,
    Iterable,
)

from starlette.requests import Request
from starlette.responses import Response

# WSGI: view PEP3333
Environ = MutableMapping[str, Any]
StartResponse = Callable[[str, Iterable[Tuple[str, str]]], None]
WSGIApp = Callable[[Environ, StartResponse], Iterable[Union[str, bytes]]]

HTTPFunc = Callable[[Request], Awaitable[Union[Response, Tuple]]]
