import asyncio
from indexpy.routing.routes import SocketRoute
from pathlib import Path as FilePath

from indexpy import websocket, HTTPException, Index, Path, required_method
from indexpy.routing import HttpRoute


async def homepage():
    """
    Homepage
    """
    return "hello, index.py"


async def exc():
    raise Exception("For get debug page.")


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


async def sources(filepath: str = Path()):
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


app = Index(
    debug=True,
    routes=[
        HttpRoute("/", homepage),
        HttpRoute("/exc", exc),
        HttpRoute("/message", message),
        HttpRoute("/sources/{filepath:path}", sources) @ required_method("GET"),
        SocketRoute("/", ws),
    ],
)
app.state.wait_time = 1
