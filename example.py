import asyncio
import os
from pathlib import Path as FilePath

from indexpy import Index, Path, HTTPException
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
            await asyncio.sleep(1)
            yield {"id": i, "data": "hello"}

    return message_gen()


async def sources(filepath: str = Path()):
    """
    Return source files
    """
    realpath = FilePath(".") / filepath.lstrip("./")
    try:
        return os.stat(realpath), str(realpath)
    except FileNotFoundError:
        raise HTTPException(404)


app = Index(debug=True)
app.router < HttpRoute("/", homepage)
app.router << [
    HttpRoute("/exc", exc),
    HttpRoute("/message", message),
]
app.router < HttpRoute("/sources/{filepath:path}", sources)
