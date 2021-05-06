from __future__ import annotations

import functools
import json
import sys
from inspect import isfunction
from typing import TYPE_CHECKING, Any, Callable, Generator, List, TypeVar
from typing import cast as typing_cast

if sys.version_info[:2] < (3, 8):
    from typing_extensions import Literal
else:
    from typing import Literal

from baize.asgi import Message

from .requests import request, websocket
from .responses import HttpResponse

FuncView = TypeVar("FuncView", bound=Callable)


def required_method(method: str) -> Callable[[FuncView], FuncView]:
    """
    Set the acceptable request method of the function
    """
    allow_methods = {"HEAD", "GET"} if method == "GET" else {method}
    headers = {"Allow": ", ".join(allow_methods)}

    def decorator(function: FuncView) -> FuncView:
        if not isfunction(function):
            raise TypeError("`required_method` can only decorate function")

        @functools.wraps(function)
        async def wrapper(*args, **kwargs):
            if request.method in allow_methods:
                return await function(*args, **kwargs)
            elif request.method == "OPTIONS":
                return HttpResponse(headers=headers)
            else:
                return HttpResponse(status_code=405, headers=headers)

        setattr(wrapper, "__method__", method.upper())
        return typing_cast(FuncView, wrapper)

    return decorator


class HttpView:
    HTTP_METHOD_NAMES = [
        "get",
        "post",
        "put",
        "patch",
        "delete",
        "head",
        "options",
        "trace",
    ]

    if TYPE_CHECKING:
        __methods__: List[str]

    def __init_subclass__(cls) -> None:
        cls.__methods__ = [m.upper() for m in cls.HTTP_METHOD_NAMES if hasattr(cls, m)]

    def __await__(self) -> Generator[None, None, Any]:
        return self.__impl__().__await__()

    async def __impl__(self) -> Any:
        handler = getattr(self, request.method.lower(), self.http_method_not_allowed)
        return await handler()

    async def http_method_not_allowed(self) -> HttpResponse:
        return HttpResponse(
            status_code=405, headers={"Allow": ", ".join(self.__methods__)}
        )

    async def options(self) -> HttpResponse:
        """Handle responding to requests for the OPTIONS HTTP verb."""
        return HttpResponse(headers={"Allow": ", ".join(self.__methods__)})


class SocketView:
    encoding: Literal["anystr", "text", "bytes", "json"] = "anystr"

    def __await__(self):
        return self.__impl__().__await__()

    async def __impl__(self) -> None:
        try:
            close_code = 1000
            await self.on_connect()
            while True:
                message = await websocket.receive()
                if message["type"] == "websocket.receive":
                    data = await self.decode(message)
                    await self.on_receive(data)
                elif message["type"] == "websocket.disconnect":
                    close_code = int(message.get("code", 1000))
                    break
        except Exception as exc:
            close_code = 1011
            raise exc
        finally:
            await self.on_disconnect(close_code)

    async def decode(self, message: Message) -> Any:
        if self.encoding == "text":
            if "text" not in message:
                await websocket.close(code=1003)
                raise RuntimeError("Expected text websocket messages, but got bytes")
            return message["text"]

        if self.encoding == "bytes":
            if "bytes" not in message:
                await websocket.close(code=1003)
                raise RuntimeError("Expected bytes websocket messages, but got text")
            return message["bytes"]

        if self.encoding == "json":
            if message.get("text") is not None:
                text = message["text"]
            else:
                text = message["bytes"].decode("utf-8")

            try:
                return json.loads(text)
            except json.decoder.JSONDecodeError:
                await websocket.close(code=1003)
                raise RuntimeError("Malformed JSON data received.")

        return message["text"] if message.get("text") else message["bytes"]

    async def on_connect(self) -> None:
        """Override to handle an incoming websocket connection"""
        await websocket.accept()

    async def on_receive(self, data: Any) -> None:
        """Override to handle an incoming websocket message"""

    async def on_disconnect(self, close_code: int) -> None:
        """Override to handle a disconnecting websocket"""
        await websocket.close(code=close_code)
