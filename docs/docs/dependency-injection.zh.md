# 依赖注入

Kuí 内置了基于 `Depends` 的依赖注入系统。依赖项通过 `Annotated` 在处理器签名中声明，在请求时自动解析。

## 基本用法

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

依赖函数 `get_db` 在处理器之前被调用，返回值作为 `db` 参数注入。

## 生成器依赖（清理）

使用生成器函数实现初始化/清理模式：

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

`yield` 之前的代码在处理器之前运行。`yield` 之后的代码（在 `finally` 中）在响应发送后运行——即使处理器抛出异常也会执行。

=== "ASGI"

    ```python
    # 异步生成器
    async def get_connection():
        conn = await pool.acquire()
        try:
            yield conn
        finally:
            await conn.release()
    ```

=== "WSGI"

    ```python
    # 同步生成器
    def get_connection():
        conn = pool.acquire()
        try:
            yield conn
        finally:
            conn.release()
    ```

ASGI 模式同时支持同步和异步生成器。WSGI 模式仅支持同步生成器。

## 缓存

默认情况下，依赖项按请求缓存（`cache=True`）。如果同一依赖在多个参数或嵌套依赖中声明，只会被调用一次：

```python
async def get_db():
    print("called")  # 每个请求只打印一次
    return db

@app.router.http.get("/")
async def handler(
    db1: Annotated[DB, Depends(get_db)],
    db2: Annotated[DB, Depends(get_db)],  # 与 db1 相同的实例
):
    assert db1 is db2
```

使用 `cache=False` 禁用缓存，每次都重新调用依赖：

```python
async def get_timestamp():
    return time.time()

@app.router.http.get("/")
async def handler(
    t1: Annotated[float, Depends(get_timestamp, cache=False)],
    t2: Annotated[float, Depends(get_timestamp, cache=False)],
):
    assert t1 != t2  # 不同的值
```

## 嵌套依赖

依赖项可以声明自己的依赖——递归解析：

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

解析顺序：`get_config` → `get_db` → `get_user_repo` → `list_users`。

## 带参数的依赖

依赖项可以使用与处理器相同的 `Annotated` 参数绑定：

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

这些参数也会包含在生成的 OpenAPI 文档中。

## 中间件中的依赖

中间件包装器也可以声明 `Annotated` 参数：

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

中间件的参数会自动从请求中提取和注入，同样会出现在 OpenAPI 文档中。

## `auto_params` 装饰器

使用 `auto_params` 在路由之外的函数上启用参数绑定（如工具函数）：

```python
from kui.asgi import auto_params

@auto_params
async def process(
    db: Annotated[DB, Depends(get_db)],
    token: Annotated[str, Header(alias="authorization")],
):
    ...
```

通常不需要使用——路由和中间件已经自动启用了参数绑定。
