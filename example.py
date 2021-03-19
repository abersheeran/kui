import asyncio
import os
from pathlib import Path as FilePath

from indexpy import Index, Path
from indexpy.exceptions import HTTPException
from indexpy.routing import HttpRoute
from indexpy.openapi import ApiView


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


class Sources(ApiView):
    async def get(filepath: str = Path()):
        """
        Return source files
        """
        realpath = FilePath(".") / filepath.split("./")
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
app.router < HttpRoute("/sources/{filepath:path}", Sources)
