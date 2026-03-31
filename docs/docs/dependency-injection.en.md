# Dependency Injection

Kuí has a built-in dependency injection system using `Depends`. Dependencies are declared in handler signatures via `Annotated` and resolved automatically at request time.

## Basic Usage

```python
from typing_extensions import Annotated
from kui.asgi import Depends

async def get_db():
    return database.connect()

@app.router.http.get("/users")
async def list_users(
    db: Annotated[Connection, Depends(get_db)],
):
    return await db.fetch("SELECT * FROM users")
```

The dependency function `get_db` is called before the handler. Its return value is injected as the `db` parameter.

## Generator Dependencies (Cleanup)

Use generator functions for setup/teardown patterns:

```python
async def get_connection():
    conn = await pool.acquire()
    try:
        yield conn
    finally:
        await conn.release()

@app.router.http.get("/")
async def handler(
    conn: Annotated[Connection, Depends(get_connection)],
):
    return await conn.fetch("SELECT 1")
```

The code before `yield` runs before the handler. The code after `yield` (in `finally`) runs after the response is sent — even if the handler raises an exception.

=== "ASGI"

    ```python
    # Async generator
    async def get_connection():
        conn = await pool.acquire()
        try:
            yield conn
        finally:
            await conn.release()
    ```

=== "WSGI"

    ```python
    # Sync generator
    def get_connection():
        conn = pool.acquire()
        try:
            yield conn
        finally:
            conn.release()
    ```

Both sync and async generators are supported in ASGI mode. Only sync generators work in WSGI mode.

## Caching

By default, dependencies are cached per request (`cache=True`). If the same dependency is declared in multiple parameters or nested dependencies, it is called only once:

```python
async def get_db():
    print("called")  # Prints only once per request
    return db

@app.router.http.get("/")
async def handler(
    db1: Annotated[DB, Depends(get_db)],
    db2: Annotated[DB, Depends(get_db)],  # Same instance as db1
):
    assert db1 is db2
```

Disable caching with `cache=False` to call the dependency fresh each time:

```python
async def get_timestamp():
    return time.time()

@app.router.http.get("/")
async def handler(
    t1: Annotated[float, Depends(get_timestamp, cache=False)],
    t2: Annotated[float, Depends(get_timestamp, cache=False)],
):
    assert t1 != t2  # Different values
```

## Nested Dependencies

Dependencies can declare their own dependencies — they are resolved recursively:

```python
async def get_config():
    return load_config()

async def get_db(config: Annotated[Config, Depends(get_config)]):
    return connect(config.database_url)

async def get_user_repo(db: Annotated[DB, Depends(get_db)]):
    return UserRepository(db)

@app.router.http.get("/users")
async def list_users(
    repo: Annotated[UserRepository, Depends(get_user_repo)],
):
    return await repo.all()
```

The resolution order is: `get_config` → `get_db` → `get_user_repo` → `list_users`.

## Dependencies with Parameters

Dependencies can use the same `Annotated` parameter binding as handlers:

```python
from kui.asgi import Header

async def verify_token(
    authorization: Annotated[str, Header(alias="authorization")],
):
    if not authorization.startswith("Bearer "):
        raise HTTPException(401)
    return decode_jwt(authorization[7:])

@app.router.http.get("/me")
async def me(
    user: Annotated[User, Depends(verify_token)],
):
    return user
```

These parameters are also included in the generated OpenAPI documentation.

## Dependencies in Middleware

Middleware wrappers can also declare `Annotated` parameters:

```python
def auth_middleware(endpoint):
    async def wrapper(
        token: Annotated[str, Header(alias="authorization")],
    ):
        verify(token)
        return await endpoint()
    return wrapper

app.router <<= HttpRoute("/admin", handler) @ auth_middleware
```

The middleware's parameters are extracted from the request and injected automatically. They also appear in OpenAPI documentation.

## The `auto_params` Decorator

Use `auto_params` to enable parameter binding on functions outside of routes (e.g., utility functions):

```python
from kui.asgi import auto_params

@auto_params
async def process(
    db: Annotated[DB, Depends(get_db)],
    token: Annotated[str, Header(alias="authorization")],
):
    ...
```

This is rarely needed — routes and middleware already have auto-binding enabled.
