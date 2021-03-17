import asyncio
from indexpy.routing.routes import SubRoutes
from pathlib import Path
import os

from indexpy import Index
from indexpy.routing import HttpRoute, Routes


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


async def readme():
    """
    Return README.md file
    """
    readme_path = str(Path(".").absolute() / "README.md")
    return os.stat(readme_path), readme_path


app = Index(
    debug=True,
    routes=[HttpRoute("/", homepage)],
)
app.router << Routes(
    HttpRoute("/exc", exc),
    HttpRoute("/message", message),
)
app.router << SubRoutes(
    "/sources",
    [
        HttpRoute("/README.md", readme),
    ],
)
