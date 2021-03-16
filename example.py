import asyncio

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
        for i in range(101):
            await asyncio.sleep(1)
            yield {"id": i, "data": "hello"}

    return message_gen()


app = Index(
    debug=True,
    routes=[HttpRoute("/", homepage)],
)
app.router << Routes(
    HttpRoute("/exc", exc),
    HttpRoute("/message", message),
)
