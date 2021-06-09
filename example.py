import asyncio
from pathlib import Path as FilePath

from indexpy import FileResponse, HTTPException, Index, Path, required_method
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


@required_method("GET")
async def sources(filepath: str = Path()):
    """
    Return source files
    """
    realpath = FilePath(".") / filepath.lstrip("./")
    try:
        return FileResponse(str(realpath))
    except FileNotFoundError:
        raise HTTPException(404)


app = Index(
    debug=True,
    routes=[
        HttpRoute("/", homepage),
        HttpRoute("/exc", exc),
        HttpRoute("/message", message),
        HttpRoute("/sources/{filepath:path}", sources),
    ],
)
app.state.wait_time = 1
