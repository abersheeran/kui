# 中间件

中间件是一个包装端点处理器的函数。它接收端点并返回一个新的处理器：

```python
def my_middleware(endpoint):
    async def wrapper():
        # 处理器之前
        print("before")
        result = await endpoint()
        # 处理器之后
        print("after")
        return result
    return wrapper
```

!!! warning
    **不要**在中间件包装器上使用 `@functools.wraps`。框架检测到后会抛出 `RuntimeError`，因为 `functools.wraps` 会复制干扰参数绑定和 OpenAPI 生成的属性。

## 应用中间件

### 使用 `@` 运算符（单路由）

```python
from kui.asgi import HttpRoute, required_method, allow_cors

route = HttpRoute("/data", handler) @ required_method("GET") @ allow_cors()
app.router <<= route
```

中间件从右到左应用：`allow_cors` 先包装，然后 `required_method`。

### 通过装饰器参数（单路由）

```python
@app.router.http.get("/data", middlewares=[my_middleware])
async def handler():
    ...
```

### 路由分组级

```python
from kui.asgi import Routes, HttpRoute

routes = Routes(
    HttpRoute("/a", handler_a),
    HttpRoute("/b", handler_b),
    http_middlewares=[auth_middleware, logging_middleware],
)
```

或使用装饰器注册：

```python
routes = Routes()

@routes.http_middleware
def logging_middleware(endpoint):
    async def wrapper():
        print(f"Request received")
        return await endpoint()
    return wrapper

@routes.http.get("/")
async def handler():
    return "ok"
```

### 应用级

```python
app = Kui(
    http_middlewares=[logging_middleware, auth_middleware],
    socket_middlewares=[ws_auth_middleware],  # 仅 ASGI
)
```

## 带参数的中间件

中间件包装器可以声明 `Annotated` 参数以自动绑定请求数据：

```python
from typing_extensions import Annotated
from kui.asgi import Header

def auth_middleware(endpoint):
    async def wrapper(
        authorization: Annotated[str, Header(alias="authorization")],
    ):
        if not verify_token(authorization):
            raise HTTPException(401)
        return await endpoint()
    return wrapper
```

这些参数会：

- 自动从请求中提取
- 通过 Pydantic 验证
- 包含在 OpenAPI 文档中

## 中间件执行顺序

中间件按以下顺序应用（从外到内）：

1. **应用级**中间件（`Kui` 上的 `http_middlewares`）
2. **路由分组级**中间件（`Routes` 上的 `http_middlewares`）
3. **单路由**中间件（通过 `@` 运算符或 `middlewares=` 参数）

处理器在最内层最后运行。

## 内置中间件

### `required_method`

限制处理器只接受特定 HTTP 方法：

```python
from kui.asgi import required_method

route = HttpRoute("/data", handler) @ required_method("GET")
```

非匹配方法返回 `405 Method Not Allowed`。`OPTIONS` 请求返回 `200` 并带有 `Allow` 头。

### `allow_cors`

单路由 CORS 中间件：

```python
from kui.asgi import allow_cors

route = HttpRoute("/api", handler) @ allow_cors(
    allow_origins=[re.compile(r"https://example\.com")],
    allow_methods=["GET", "POST"],
    allow_headers=["Authorization"],
    max_age=600,
)
```

详见 [CORS](cors.md)。

## 示例：计时中间件

```python
import time

def timing_middleware(endpoint):
    async def wrapper():
        start = time.monotonic()
        response = await endpoint()
        elapsed = time.monotonic() - start
        print(f"Request took {elapsed:.3f}s")
        return response
    return wrapper

app = Kui(http_middlewares=[timing_middleware])
```
