# Lifespan

!!! note
    Lifespan events are only available in ASGI mode. WSGI does not support startup/shutdown hooks.

Lifespan events let you run code when the application starts up and shuts down — useful for initializing database pools, caches, or other shared resources.

## Async Generator (Recommended)

Pass an async generator function to `Kui(lifespan=...)`. Code before `yield` runs on startup; code after `yield` runs on shutdown:

```python
from kui.asgi import Kui

async def lifespan(app: Kui):
    # Startup
    app.state.db = await create_pool()
    app.state.redis = await create_redis()
    yield
    # Shutdown
    await app.state.redis.close()
    await app.state.db.close()

app = Kui(lifespan=lifespan)
```

This keeps related setup/teardown logic together in one function.

## Application State

Use `app.state` to store shared resources initialized during lifespan:

```python
async def lifespan(app: Kui):
    app.state.db = await asyncpg.create_pool(DATABASE_URL)
    app.state.redis = await aioredis.create_pool("redis://localhost")
    yield
    await app.state.redis.close()
    await app.state.db.close()

app = Kui(lifespan=lifespan)
```

Access in handlers via `request.app.state`:

```python
@app.router.http.get("/")
async def handler():
    db = request.app.state.db
    return await db.fetch("SELECT 1")
```

## Graceful Shutdown

Set `app.should_exit = True` to signal the server to shut down gracefully:

```python
@app.router.http.post("/shutdown")
async def shutdown_endpoint():
    request.app.should_exit = True
    return {"status": "shutting down"}
```

This requires server support (e.g., uvicorn checks this flag).

## Deprecated: on_startup / on_shutdown

!!! warning "Deprecated"
    `on_startup` and `on_shutdown` are deprecated. Use the `lifespan` async generator instead.

The old callback-based API still works but emits a `DeprecationWarning`:

```python
# Deprecated — avoid in new code
app = Kui(
    on_startup=[init_db],
    on_shutdown=[close_db],
)

# Also deprecated
@app.on_startup
async def startup(app: Kui): ...

@app.on_shutdown
async def shutdown(app: Kui): ...
```

You cannot mix `lifespan` with `on_startup`/`on_shutdown` — this raises `ValueError`.

`asynccontextmanager_lifespan` is also deprecated. Replace:

```python
# Old
from kui.asgi.lifespan import asynccontextmanager_lifespan
on_startup, on_shutdown = asynccontextmanager_lifespan(my_func)
app = Kui(on_startup=[on_startup], on_shutdown=[on_shutdown])

# New
app = Kui(lifespan=my_func)
```
