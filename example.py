import asyncio

from indexpy import Index, request
from indexpy.__version__ import __version__
from indexpy.openapi import OpenAPI, describe_response
from indexpy.responses import SendEventResponse
from indexpy.routing import Routes, SubRoutes

app = Index(debug=True)


@app.router.http("/")
@describe_response(
    200,
    content={"text/plain": {"schema": {"type": "string"}}},
)
async def homepage():
    """
    Homepage
    """
    return "hello, index.py"


@app.router.http("/exc")
async def exc():
    raise Exception("For get debug page.")


@app.router.http("/message")
@describe_response(200, content={"text/event-stream": {}})
async def message():
    """
    Message

    For testing server send event response
    """

    async def message_gen():
        for i in range(101):
            await asyncio.sleep(1)
            yield {"id": i, "data": "hello"}

    return SendEventResponse(message_gen())
