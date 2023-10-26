## 初始化参数

除去本文档其他地方提到的参数外，`Kui` 还支持以下初始化参数。

### `http_middlewares`

此参数用于添加全局 HTTP 中间件。

### `socket_middlewares`

此参数用于添加全局 WebSocket 中间件。

### `factory_class`

此参数用于自定义 HttpRequest、WebSocket 类。

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

## 属性

### `state`

`app.state` 用于存储全局变量。以下是结合 [Lifespan](../lifespan/) 使用 redis 的样例。

```python
import redis.asyncio
from kui.asgi import Kui


async def init_redis(app: Kui)
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

`app.should_exit` 用于指示 Application 是否将被关闭。

!!! notice
    该属性需要启动的服务器支持。

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
