# WSGI 模式

Kuí 同时支持 ASGI 和 WSGI。两者 API 几乎完全一致——本页记录其差异。

## 何时使用 WSGI

- 应用完全同步
- 不需要 WebSocket 或生命周期事件
- 想使用成熟的 WSGI 服务器（Gunicorn、uWSGI 等）
- 部署环境要求 WSGI

## 与 ASGI 的差异

| 特性 | ASGI | WSGI |
|---|---|---|
| 导入 | `from kui.asgi import ...` | `from kui.wsgi import ...` |
| 处理器 | `async def handler():` | `def handler():` |
| 依赖项 | `async def` 或 `def` | 仅 `def` |
| 生成器依赖 | `async def` 生成器 | `def` 生成器 |
| WebSocket | 支持（`SocketRoute`、`SocketView`） | 不可用 |
| 生命周期 | 支持（`on_startup`、`on_shutdown`） | 不可用 |
| `socket_middlewares` | 支持 | 不可用 |
| Server-Sent Events | `SendEventResponse` | `SendEventResponse` |
| 其他功能 | 相同 API | 相同 API |

## 快速开始

```python
from typing_extensions import Annotated
from kui.wsgi import Kui, OpenAPI, HttpRoute, Path, Query, Body

def hello():
    return {"message": "Hello, Kuí!"}

def greet(name: Annotated[str, Path()]):
    return {"message": f"Hello, {name}!"}

app = Kui(routes=[
    HttpRoute("/", hello),
    HttpRoute("/greet/{name}", greet),
])

app.router <<= "/docs" // OpenAPI(
    info={"title": "My API", "version": "1.0.0"},
    template_name="swagger",
).routes
```

运行：

```bash
gunicorn app:app
```

## WSGI 处理器示例

### 函数处理器

```python
from kui.wsgi import request

@app.router.http.get("/users")
def list_users():
    return [{"id": 1, "name": "Alice"}]

@app.router.http.post("/users")
def create_user(user: Annotated[UserCreate, Body(exclusive=True)]):
    return user, 201
```

### 基于类的视图

```python
from kui.wsgi import HttpView

@app.router.http("/users")
class UserView(HttpView):

    @classmethod
    def get(cls):
        return []

    @classmethod
    def post(cls):
        return {}, 201
```

### 访问请求

```python
from kui.wsgi import request

@app.router.http.get("/info")
def info():
    return {
        "method": request.method,
        "path": request.url.path,
    }
```

请求体解析是同步的：

```python
body = request.body    # bytes（缓存属性）
data = request.json    # 解析后的 JSON（缓存属性）
form = request.form    # 解析后的表单数据（缓存属性）
data = request.data()  # 自动检测格式（方法调用）
```

!!! note
    `body`、`json` 和 `form` 是缓存属性（无括号）。只有 `data()` 是方法调用。

### 依赖注入

```python
from kui.wsgi import Depends

def get_db():
    return database.connect()

# 带清理的生成器依赖
def get_connection():
    conn = pool.acquire()
    try:
        yield conn
    finally:
        conn.release()

@app.router.http.get("/")
def handler(conn: Annotated[Connection, Depends(get_connection)]):
    return conn.fetch("SELECT 1")
```

### 文件上传

```python
from kui.wsgi import UploadFile

@app.router.http.post("/upload")
def upload(file: Annotated[UploadFile, Body(...)]):
    content = file.read()  # 同步读取
    return {"filename": file.filename, "size": len(content)}
```

### 自定义响应转换器

```python
app = Kui(
    response_converters={
        MyType: lambda obj, status=200, headers=None: JSONResponse(
            obj.to_dict(), status, headers
        ),
    }
)
```

## 应用配置

WSGI 的 `Kui` 接受与 ASGI 相同的参数，但不包括：

- 没有 `on_startup` / `on_shutdown`
- 没有 `socket_middlewares`

```python
from kui.wsgi import Kui, FactoryClass, HttpRequest

class CustomRequest(HttpRequest):
    ...

app = Kui(
    routes=[...],
    http_middlewares=[...],
    cors_config={...},
    exception_handlers={...},
    factory_class=FactoryClass(http=CustomRequest),
    response_converters={...},
    json_encoder={...},
    templates=templates,
)
```

## 可用导出

WSGI 导出与 ASGI 相同的符号，减去 WebSocket 相关的：

- 没有：`WebSocket`、`websocket`、`websocket_var`、`SocketView`
- `SocketRoute` 已导出但在 WSGI 中无实际用途（无 WebSocket 服务器支持）
- 其他全部可用：`Kui`、`OpenAPI`、`HttpRoute`、`Routes`、`MultimethodRoutes`、`HttpView`、`Path`、`Query`、`Header`、`Cookie`、`Body`、`Depends`、`UploadFile`、`request`、`HTTPException`、`allow_cors`、`required_method`、`bearer_auth`、`basic_auth`、`api_key_auth_dependency`、所有响应类等。
