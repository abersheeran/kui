import asyncio
from pathlib import Path as FilePath

from typing_extensions import Annotated

from kui.asgi import (
    HTTPException,
    HttpRoute,
    Kui,
    SocketRoute,
    required_method,
    websocket,
    Path,
    allow_cors,
    OpenAPI,
)


async def homepage():
    """
    Homepage
    """
    return "Kuí"


async def message():
    """
    Message

    For testing server send event response
    """

    async def message_gen():
        for i in range(5):
            await asyncio.sleep(app.state.wait_time)
            yield {"id": i, "data": "hello"}

    return message_gen()


async def sources(filepath: Annotated[str, Path()]):
    """
    Return source files
    """
    realpath = FilePath(".") / filepath.lstrip("./")
    if realpath.exists() and realpath.is_file():
        return realpath
    else:
        raise HTTPException(404)


async def ws():
    await websocket.accept()
    while not await websocket.is_disconnected():
        await websocket.send_json({"data": "(^_^)"})
        await asyncio.sleep(app.state.wait_time)
    await websocket.close()


app = Kui(
    routes=[
        HttpRoute("/", homepage),
        HttpRoute("/message", message),
        HttpRoute("/sources/{filepath:any}", sources) @ required_method("GET"),
        SocketRoute("/", ws),
    ],
    http_middlewares=[
        allow_cors(),
    ],
)
app.router <<= "/docs" // OpenAPI(template_name="redoc").routes
app.state.wait_time = 1
