import os
import asyncio

from indexpy import Index, Config
from indexpy.http.responses import EventResponse

os.environ["INDEX_DEBUG"] = "on"
Config().import_from_environ()

app = Index()


@app.router.http("/", method="get")
async def homepage(request):
    return "hello, index.py"


@app.router.http("/exc", method="get")
async def exc(rq):
    raise Exception("For get debug page.")


@app.router.http("/message", method="get")
async def message(request):
    async def message_gen():
        for _ in range(101):
            await asyncio.sleep(1)
            yield "event: message\r\ndata: {'name': 'Aber', 'body': 'hello'}"

    return EventResponse(message_gen())
