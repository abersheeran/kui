import asyncio

import uvicorn

from kui.asgi import Kui, websocket

# See https://stackoverflow.com/questions/58133694/graceful-shutdown-of-uvicorn-starlette-app-with-websockets
origin_handle_exit = uvicorn.Server.handle_exit


def handle_exit(self: uvicorn.Server, sig, frame):
    application = self.config.loaded_app
    while not isinstance(application, Kui):
        application = application.app
    application.should_exit = True
    return origin_handle_exit(self, sig, frame)


uvicorn.Server.handle_exit = handle_exit


app = Kui()


@app.router.websocket("/ws")
async def ws():
    await websocket.accept()

    while not websocket.app.should_exit:
        await asyncio.sleep(0.1)

    await websocket.close()


if __name__ == "__main__":
    uvicorn.run(app, port=12345)
