## Initializing Parameters

In addition to the parameters mentioned elsewhere in this document, `Kui` also supports the following initialization parameters.

### `http_middlewares`

This parameter is used to add global HTTP middlewares.

### `socket_middlewares`

This parameter is used to add global WebSocket middlewares.

### `factory_class`

This parameter is used to customize the `HttpRequest` and `WebSocket` classes.

```python
from kui.asgi import Kui, HttpRequest, WebSocket


class CustomHttpRequest(HttpRequest):
    ...


class CustomWebSocket(WebSocket):
    ...


app = Kui(
    factory_class=FactoryClass(http=CustomHttpRequest, websocket=CustomWebSocket),
)
```

## Attributes

### `state`

`app.state` is used to store global variables. Here is an example using Redis in conjunction with [Lifespan](../lifespan/).

```python
import redis.asyncio
from kui.asgi import Kui


async def init_redis(app: Kui):
    app.state.redis = redis.asyncio.Redis.from_url(
        os.environ.get("REDIS_URL", "redis://localhost:6379/0"),
        decode_responses=True,
    )


async def close_redis(app: Kui):
    await app.state.redis.close()


app = Kui(
    on_startup=[init_redis],
    on_shutdown=[close_redis],
)
```

### `should_exit`

`app.should_exit` is used to indicate whether the Application should be closed.

!!! notice
    This attribute requires support from the server being started.

    ```python
    from kui.asgi import Kui, websocket

    app = Kui()


    @app.router.websocket('/ws')
    async def ws():
        await websocket.accept()

        while not websocket.app.should_exit:
            await asyncio.sleep(0.1)

        await websocket.close()


    if __name__ == "__main__":
        # See https://stackoverflow.com/questions/58133694/graceful-shutdown-of-uvicorn-starlette-app-with-websockets
        origin_handle_exit = uvicorn.Server.handle_exit

        def handle_exit(self: uvicorn.Server, sig, frame):
            app.should_exit = True
            return origin_handle_exit(self, sig, frame)

        uvicorn.Server.handle_exit = handle_exit

        uvicorn.run(app)
    ```
