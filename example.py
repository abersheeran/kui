import asyncio

from indexpy import Index
from indexpy.__version__ import __version__
from indexpy.http.responses import ServerSendEventResponse
from indexpy.openapi import OpenAPI, describe_response
from indexpy.routing import Routes, SubRoutes

app = Index(
    debug=True,
    routes=Routes(
        SubRoutes(
            "/openapi",
            OpenAPI(
                "Index.py Example",
                "Just a simple example, and for display debug page.",
                __version__,
            ).routes,
            namespace="openapi",
        )
    ),
)


@app.router.http("/", method="get")
@describe_response(
    200,
    content={"text/plain": {"schema": {"type": "string"}}},
)
async def homepage(request):
    """
    Homepage
    """
    return "hello, index.py"


@app.router.http("/exc", method="get")
async def exc(rq):
    raise Exception("For get debug page.")


@app.router.http("/message", method="get")
@describe_response(
    200,
    content={"text/event-stream": {"schema": {"type": "string"}}},
)
async def message(request):
    """
    Message

    For testing server send event response
    """

    async def message_gen():
        for _ in range(101):
            await asyncio.sleep(1)
            yield "\r\n".join(
                map(
                    lambda line: line.strip(),
                    f"""id:{_}
                    event: message
                    data: {{'name': 'Aber', 'body': 'hello'}}
                    """.splitlines(),
                )
            )

    return ServerSendEventResponse(message_gen())
