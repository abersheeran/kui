# 路由

Kuí 使用 **基数树**（压缩前缀树）进行快速路由匹配。

## 路由注册

### 装饰器风格

最常用的路由注册方式：

```python
from kui.asgi import Kui

app = Kui()

# 任意 HTTP 方法
@app.router.http("/health")
async def health():
    return "ok"

# 指定方法
@app.router.http.get("/users")
async def list_users():
    return []

@app.router.http.post("/users")
async def create_user():
    return {}, 201
```

可用的方法快捷方式：`.get()`、`.post()`、`.put()`、`.patch()`、`.delete()`。

装饰器参数：

| 参数 | 类型 | 说明 |
|---|---|---|
| `path` | `str` | URL 路径模式 |
| `name` | `str` | 路由名称，用于 URL 反查 |
| `middlewares` | `list` | 路由级中间件列表 |
| `summary` | `str` | OpenAPI 操作摘要 |
| `description` | `str` | OpenAPI 操作描述 |
| `tags` | `list[str]` | OpenAPI 标签 |

### 路由对象与 `<<` 运算符

```python
from kui.asgi import HttpRoute, SocketRoute

app.router <<= HttpRoute("/", homepage)
app.router <<= SocketRoute("/ws", ws_handler)

# 链式添加多个路由
app.router <<= (
    app.router
    << HttpRoute("/a", handler_a)
    << HttpRoute("/b", handler_b)
)
```

`HttpRoute` 接受参数：`path`、`endpoint`、`name`、`summary`、`description`、`tags`。

### Routes 容器

将路由分组并共享配置：

```python
from kui.asgi import Routes, HttpRoute

api_routes = Routes(
    HttpRoute("/users", list_users),
    HttpRoute("/posts", list_posts),
    namespace="api",              # 路由名称前缀
    tags=["API"],                 # 所有路由的 OpenAPI 标签
    http_middlewares=[auth_mw],   # 共享中间件
)
```

`Routes` 支持 `<<` 和 `+` 运算符：

```python
routes = Routes(HttpRoute("/a", a))
routes <<= HttpRoute("/b", b)

combined = routes_a + routes_b
```

Routes 也支持切片操作：`routes[1:3]`。

## 路径参数

路径参数使用 `{name}` 或 `{name:type}` 语法声明：

| 类型 | 语法 | 匹配 | 示例 |
|---|---|---|---|
| `str`（默认） | `{name}` | 除 `/` 外的任意字符串 | `/users/alice` |
| `int` | `{name:int}` | 整数 | `/users/42` |
| `decimal` | `{name:decimal}` | 十进制数 | `/price/19.99` |
| `date` | `{name:date}` | 日期字符串 | `/events/2024-01-15` |
| `uuid` | `{name:uuid}` | UUID 字符串 | `/items/550e8400-...` |
| `any` | `{name:any}` | 任意内容（包括 `/`） | `/files/path/to/file.txt` |

!!! note
    `{name:any}` 必须位于路径末尾。静态路由优先于动态路由（例如 `/users/me` 会优先匹配 `/users/{id}`）。

```python
@app.router.http.get("/users/{user_id:int}")
async def get_user(user_id: Annotated[int, Path()]):
    return {"id": user_id}

@app.router.http.get("/files/{filepath:any}")
async def get_file(filepath: Annotated[str, Path()]):
    return FilePath(filepath)
```

## 通用前缀与 `//` 运算符

为一组路由添加共享前缀：

```python
from kui.asgi import Routes, HttpRoute

api = Routes(
    HttpRoute("/users", list_users),
    HttpRoute("/posts", list_posts),
)

# 所有路由添加 /api/v1 前缀
app.router <<= "/api/v1" // api
# 结果：/api/v1/users、/api/v1/posts
```

同样适用于 OpenAPI 路由：

```python
from kui.asgi import OpenAPI

app.router <<= "/docs" // OpenAPI(template_name="swagger").routes
```

## 反向 URL 查询

通过路由名称生成 URL：

```python
app.router <<= HttpRoute("/users/{user_id:int}", get_user, name="user-detail")

url = app.router.url_for("user-detail", {"user_id": 42})
# 返回："/users/42"
```

在处理器中使用 `request.url_for()`：

```python
from kui.asgi import request

@app.router.http.get("/")
async def homepage():
    user_url = request.url_for("user-detail", {"user_id": 1})
    return {"user_url": str(user_url)}
```

## 路由中间件

使用 `@` 运算符为单个路由应用中间件：

```python
from kui.asgi import HttpRoute, required_method, allow_cors

route = HttpRoute("/data", handler) @ required_method("GET") @ allow_cors()
app.router <<= route
```

或在装饰器中传入中间件：

```python
@app.router.http.get("/data", middlewares=[allow_cors()])
async def handler():
    ...
```

详见[中间件](middleware.md)了解编写和应用中间件的方法。

## MultimethodRoutes

将同一路径的多个单方法处理器自动合并为一个视图：

```python
from kui.asgi import MultimethodRoutes as Routes, HttpView

routes = Routes(base_class=HttpView)

@routes.http.get("/users")
async def list_users():
    return []

@routes.http.post("/users")
async def create_user():
    return {}, 201

@routes.http.delete("/users/{user_id:int}")
async def delete_user():
    return "", 204

app.router <<= routes
```

这等同于编写基于类的 `HttpView`，但允许你将处理器保持为独立函数。内部会自动将它们合并为一个视图类。

## WebSocket 路由

仅 ASGI 模式。注册 WebSocket 处理器：

```python
@app.router.websocket("/ws")
async def ws_handler():
    await websocket.accept()
    data = await websocket.receive_json()
    await websocket.send_json({"echo": data})
    await websocket.close()
```

或使用路由对象：

```python
app.router <<= SocketRoute("/ws", ws_handler)
```

完整文档请参见 [WebSocket](websocket.md)。

## 命令行：显示路由

从命令行查看所有已注册的路由：

```bash
python -m kui.routing your_module:app
```
