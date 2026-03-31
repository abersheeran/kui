# 生命周期

!!! note
    生命周期事件仅在 ASGI 模式下可用。WSGI 不支持 startup/shutdown 钩子。

生命周期事件让你在应用启动和关闭时运行代码——用于初始化数据库连接池、缓存或其他共享资源。

## 异步生成器（推荐）

将异步生成器函数传递给 `Kui(lifespan=...)`。`yield` 之前的代码在启动时运行；`yield` 之后的代码在关闭时运行：

```python
from kui.asgi import Kui

async def lifespan(app: Kui):
    # 启动
    app.state.db = await create_pool()
    app.state.redis = await create_redis()
    yield
    # 关闭
    await app.state.redis.close()
    await app.state.db.close()

app = Kui(lifespan=lifespan)
```

这将相关的初始化/清理逻辑放在一个函数中。

## 应用状态

使用 `app.state` 存储在生命周期期间初始化的共享资源：

```python
async def lifespan(app: Kui):
    app.state.db = await asyncpg.create_pool(DATABASE_URL)
    app.state.redis = await aioredis.create_pool("redis://localhost")
    yield
    await app.state.redis.close()
    await app.state.db.close()

app = Kui(lifespan=lifespan)
```

在处理器中通过 `request.app.state` 访问：

```python
@app.router.http.get("/")
async def handler():
    db = request.app.state.db
    return await db.fetch("SELECT 1")
```

## 优雅关闭

设置 `app.should_exit = True` 通知服务器优雅关闭：

```python
@app.router.http.post("/shutdown")
async def shutdown_endpoint():
    request.app.should_exit = True
    return {"status": "shutting down"}
```

这需要服务器支持（例如 uvicorn 会检查此标志）。

## 已弃用：on_startup / on_shutdown

!!! warning "已弃用"
    `on_startup` 和 `on_shutdown` 已弃用。请改用 `lifespan` 异步生成器。

旧的回调式 API 仍然可用，但会发出 `DeprecationWarning`：

```python
# 已弃用——新代码请避免使用
app = Kui(
    on_startup=[init_db],
    on_shutdown=[close_db],
)

# 同样已弃用
@app.on_startup
async def startup(app: Kui): ...

@app.on_shutdown
async def shutdown(app: Kui): ...
```

不能同时使用 `lifespan` 和 `on_startup`/`on_shutdown`——这会引发 `ValueError`。

`asynccontextmanager_lifespan` 同样已弃用。替换方式：

```python
# 旧写法
from kui.asgi.lifespan import asynccontextmanager_lifespan
on_startup, on_shutdown = asynccontextmanager_lifespan(my_func)
app = Kui(on_startup=[on_startup], on_shutdown=[on_shutdown])

# 新写法
app = Kui(lifespan=my_func)
```
