# HTTP

## 处理器

### 函数处理器

处理 HTTP 请求最简单的方式：

```python
from kui.asgi import Kui

app = Kui()

@app.router.http.get("/")
async def homepage():
    return {"message": "Hello!"}
```

处理器可以返回多种类型，框架会自动转换为响应（参见下方[响应转换](#响应转换)）。

### 基于类的视图（HttpView）

用于处理多个 HTTP 方法的端点：

```python
from kui.asgi import HttpView

@app.router.http("/users")
class UserView(HttpView):

    @classmethod
    async def get(cls):
        return [{"id": 1, "name": "Alice"}]

    @classmethod
    async def post(cls):
        return {"created": True}, 201

    @classmethod
    async def delete(cls):
        return "", 204
```

支持的方法：`get`、`post`、`put`、`patch`、`delete`、`head`、`options`、`trace`。

- 未定义 `OPTIONS` 时会自动生成，带有 `Allow` 头。
- 不支持的方法返回 `405 Method Not Allowed`。
- 每个方法都是 `@classmethod`（ASGI：`async`，WSGI：同步）。

### 方法限制

将函数处理器限制为特定 HTTP 方法：

```python
from kui.asgi import HttpRoute, required_method

app.router <<= HttpRoute("/data", handler) @ required_method("GET")
```

非匹配方法返回 `405`，`OPTIONS` 返回 `200`。

## 请求对象

通过 `request` 上下文变量访问当前请求——无需参数：

```python
from kui.asgi import request

@app.router.http.get("/info")
async def info():
    return {
        "method": request.method,
        "url": str(request.url),
        "path": request.url.path,
    }
```

### 请求属性

| 属性 | 类型 | 说明 |
|---|---|---|
| `request.method` | `str` | HTTP 方法（`GET`、`POST` 等） |
| `request.url` | `URL` | 完整 URL 对象（`.path`、`.query`、`.scheme`、`.host`） |
| `request.headers` | `Headers` | 大小写不敏感的头部映射 |
| `request.query_params` | `QueryParams` | 查询字符串参数 |
| `request.path_params` | `dict` | 提取的路径参数 |
| `request.cookies` | `dict` | Cookie 映射 |
| `request.client` | `Address` | 客户端地址（`.host`、`.port`） |
| `request.state` | `State` | 每次请求的可变状态 |
| `request.app` | `Kui` | 应用实例 |

### 请求体

```python
# 原始字节（缓存属性，不是方法调用）
body = await request.body

# JSON（缓存属性）
data = await request.json

# 表单数据（缓存属性）
form = await request.form

# 根据 Content-Type 自动检测格式（方法调用）
data = await request.data()
```

!!! note
    ASGI 模式下，`body`、`json` 和 `form` 是可等待的缓存属性（使用 `await request.body` 而非 `await request.body()`）。只有 `data()` 是方法调用。

!!! tip
    建议使用[参数绑定](parameters.md)而非手动解析请求体。它提供自动验证和 OpenAPI 文档生成。

### 文件上传

```python
form = await request.form
upload = form["file"]  # UploadFile 对象
content = await upload.aread()
filename = upload.filename
content_type = upload.content_type
```

### 请求级状态

通过 `request.state` 存储请求范围的数据：

```python
# 写入
request.state.user = current_user

# 读取
name = request.state.user.name

# 删除
del request.state.user
```

`State` 支持同步和异步上下文管理器以实现线程安全访问：

```python
async with request.state as state:
    state.counter = state.get("counter", 0) + 1
```

### 后台任务

将响应发送后执行的任务加入队列：

```python
@app.router.http.post("/notify")
async def notify():
    request.background_tasks.append(send_email, to="user@example.com")
    return {"status": "queued"}
```

详见[后台任务](background-tasks.md)。

## 响应类型

### 自动响应转换

处理器可以返回普通 Python 值——框架会自动转换：

| 返回类型 | 转换为 |
|---|---|
| `str`、`bytes` | `PlainTextResponse` |
| `dict`、`list` | `JSONResponse` |
| `pydantic.BaseModel` | `JSONResponse` |
| `pathlib.PurePath` | `FileResponse` |
| `baize.datastructures.URL` | `RedirectResponse` |
| `AsyncGenerator`（ASGI）/ `Generator`（WSGI） | `SendEventResponse` |
| `HttpResponse` 子类 | 直接使用 |

### 通过元组设置状态码和头部

返回元组来设置状态码和头部：

```python
# (body, status_code)
return {"id": 1}, 201

# (body, status_code, headers)
return {"id": 1}, 201, {"X-Custom": "value"}
```

### 响应类

需要完全控制时直接使用响应类：

```python
from kui.asgi import (
    HttpResponse,
    PlainTextResponse,
    HTMLResponse,
    JSONResponse,
    RedirectResponse,
    StreamResponse,
    FileResponse,
    SendEventResponse,
    TemplateResponse,
)
```

#### PlainTextResponse

```python
return PlainTextResponse("Hello", status_code=200)
```

#### HTMLResponse

```python
return HTMLResponse("<h1>Hello</h1>")
```

#### JSONResponse

```python
return JSONResponse({"key": "value"}, status_code=200)
```

#### RedirectResponse

```python
return RedirectResponse("/new-location", status_code=301)
```

#### FileResponse

```python
return FileResponse("/path/to/file.pdf")
```

自动支持 `Range` 请求（状态码 206）。

#### StreamResponse

```python
async def stream():
    for chunk in data_chunks:
        yield chunk

return StreamResponse(stream())
```

#### SendEventResponse（Server-Sent Events）

```python
async def events():
    for i in range(10):
        yield {"id": i, "data": "hello"}
        await asyncio.sleep(1)

return SendEventResponse(events())
```

或从处理器直接返回异步生成器——自动转换：

```python
@app.router.http.get("/events")
async def sse():
    async def generate():
        for i in range(5):
            yield {"id": i, "data": "tick"}
            await asyncio.sleep(1)
    return generate()
```

#### TemplateResponse

```python
from kui.asgi import TemplateResponse, request

return TemplateResponse("index.html", {"request": request, "name": "World"})
```

需要配置 Jinja2 模板。详见[模板](templates.md)。

### HttpResponse 基类

所有响应类继承自 `HttpResponse`，提供：

```python
response = HttpResponse(content=b"data", status_code=200)
response.headers["X-Custom"] = "value"
response.set_cookie("session", "abc123", max_age=3600, httponly=True)
response.delete_cookie("old_cookie")
```

### 自定义响应转换器

注册自定义类型到响应的转换器：

```python
from dataclasses import dataclass

@dataclass
class ApiError:
    code: int
    message: str

app = Kui(
    response_converters={
        ApiError: lambda e, status=400, headers=None: JSONResponse(
            {"code": e.code, "message": e.message}, status, headers
        ),
    }
)
```

### 主动转换

使用 `convert_response(value)` 在正常处理器返回流程之外显式触发响应转换：

```python
from kui.asgi import convert_response

response = convert_response({"key": "value"})
```

## OpenAPI 响应文档

使用返回类型注解为 OpenAPI 记录响应类型：

```python
from typing import Any
from typing_extensions import Annotated

@app.router.http.get("/users")
async def list_users() -> Annotated[Any, JSONResponse[200, {}, list[UserModel]]]:
    return [...]
```

响应类下标语法：

```python
# 仅状态码
JSONResponse[200]

# 状态码 + 头部
JSONResponse[200, {"X-Custom": {"schema": {"type": "string"}}}]

# 状态码 + 头部 + 响应体 Schema
JSONResponse[200, {}, UserModel]
```

可用于：`JSONResponse`、`HTMLResponse`、`PlainTextResponse`、`FileResponse`、`RedirectResponse`、`SendEventResponse`、`StreamResponse`。

更多信息请参见 [OpenAPI 文档](openapi.md)。
