# OpenAPI 文档

Kuí 从代码中自动生成 [OpenAPI 3.1.0](https://spec.openapis.org/oas/v3.1.0) 文档——包括类型注解、文档字符串和路由元数据。

## 配置

```python
from kui.asgi import Kui, OpenAPI

app = Kui()

openapi = OpenAPI(
    info={"title": "My API", "version": "1.0.0"},
    template_name="swagger",      # "swagger" | "redoc" | "rapidoc"
    security_schemes={},           # 可选：自定义 OpenAPI 安全方案
)

# 挂载到 /docs
app.router <<= "/docs" // openapi.routes
```

提供以下端点：

| 路径 | 说明 |
|---|---|
| `GET /docs/` | 交互式 HTML 界面 |
| `GET /docs/json` | OpenAPI 3.1.0 JSON Schema |
| `GET /docs/heartbeat` | 热重载 SSE 端点 |

### UI 选项

| 模板 | 说明 |
|---|---|
| `"swagger"` | [Swagger UI](https://swagger.io/tools/swagger-ui/) — 交互式，支持 "Try it out" |
| `"redoc"` | [ReDoc](https://redocly.github.io/redoc/) — 简洁的只读文档 |
| `"rapidoc"` | [RapiDoc](https://rapidocweb.com/) — 现代化、可定制 |

也可以提供自定义 HTML 模板：

```python
openapi = OpenAPI(
    info={"title": "My API", "version": "1.0.0"},
    template="<html>...</html>",  # 自定义 HTML 字符串
)
```

### 重载模式

设置 `reload=True` 在每次请求时重新生成规格（开发阶段有用）：

```python
openapi = OpenAPI(info={"title": "My API", "version": "1.0.0"}, reload=True)
```

## 自动生成的文档

### 从文档字符串

处理器的文档字符串生成 `summary` 和 `description`：

```python
@app.router.http.get("/users")
async def list_users():
    """
    列出所有用户

    返回所有已注册用户的分页列表。
    支持按状态和角色过滤。
    """
    return [...]
```

- 第一段 → `summary`
- 其余文本 → `description`

### 从路由参数

```python
@app.router.http.get("/users", summary="列出用户", description="...", tags=["Users"])
async def list_users():
    ...
```

### 从参数绑定

使用 `Annotated` 声明的参数会自动生成文档：

```python
@app.router.http.get("/users")
async def list_users(
    page: Annotated[int, Query(1, ge=1, description="页码")],
    size: Annotated[int, Query(20, ge=1, le=100, description="每页数量")],
):
    ...
```

生成包含类型、位置、默认值、约束和描述的 OpenAPI `parameters` 条目。

### 从请求体参数

`Body()` 中的 Pydantic 模型生成带有 JSON Schema 的 `requestBody`：

```python
class UserCreate(BaseModel):
    name: str
    email: str

@app.router.http.post("/users")
async def create_user(user: Annotated[UserCreate, Body(exclusive=True)]):
    ...
```

### 从依赖项

依赖函数中声明的参数也会出现在文档中：

```python
async def verify_token(token: Annotated[str, Header(alias="authorization")]):
    ...

@app.router.http.get("/me")
async def me(user: Annotated[User, Depends(verify_token)]):
    ...
```

`authorization` 头部参数会出现在 `/me` 的 OpenAPI 规格中。

## 响应文档

使用返回类型注解记录响应类型：

```python
from typing import Any
from typing_extensions import Annotated
from kui.asgi import JSONResponse

@app.router.http.get("/users")
async def list_users() -> Annotated[Any, JSONResponse[200, {}, list[UserModel]]]:
    return [...]
```

### 响应下标语法

```python
# 仅状态码
JSONResponse[200]

# 状态码 + 头部
JSONResponse[200, {"X-Request-Id": {"schema": {"type": "string"}}}]

# 状态码 + 头部 + 响应体 Schema
JSONResponse[200, {}, UserModel]
```

可用响应类：`JSONResponse`、`HTMLResponse`、`PlainTextResponse`、`FileResponse`、`RedirectResponse`、`SendEventResponse`、`StreamResponse`。

### 多种响应类型

组合多个响应注解：

```python
from http import HTTPStatus

@app.router.http.get("/users/{user_id:int}")
async def get_user() -> Annotated[
    Any,
    JSONResponse[200, {}, UserModel],
    JSONResponse[HTTPStatus.NOT_FOUND],
]:
    ...
```

## 标签

### 单个路由

```python
@app.router.http.get("/users", tags=["Users"])
async def list_users():
    ...
```

### 路由分组

```python
routes = Routes(
    HttpRoute("/users", list_users),
    HttpRoute("/posts", list_posts),
    tags=["API"],
)
```

### 标签描述和路径

在 `OpenAPI` 构造函数中配置标签描述和路径映射：

```python
openapi = OpenAPI(
    info={"title": "My API", "version": "1.0.0"},
    tags={
        "Users": {"description": "用户管理端点"},
        "Posts": {
            "description": "博客文章端点",
            "paths": ["/posts", "/posts/{post_id}"],  # 自动标记这些路径
        },
    },
)
```

每个标签条目接受：

- `description`（必填）— OpenAPI 规格中的标签描述
- `paths`（可选）— 路径字符串列表；匹配这些路径的路由会自动添加标签

## 安全方案

安全依赖（Bearer、Basic、API Key）会自动生成文档：

```python
from kui.asgi import Depends, bearer_auth

@app.router.http.get("/me")
async def me(token: Annotated[str, Depends(bearer_auth)]):
    ...
```

这会在 OpenAPI `components` 中生成 `securitySchemes` 条目，并在操作上生成 `security` 要求。

详见[安全](security.md)了解所有认证选项。

## 补充文档

使用 `describe_extra_docs` 补充端点的自动生成文档：

```python
from kui.openapi import describe_extra_docs

@app.router.http.get("/users")
async def list_users():
    ...

describe_extra_docs(list_users, {
    "responses": {
        "500": {"description": "内部服务器错误"},
    },
    "deprecated": True,
})
```

`describe_extra_docs(handler, info)` 接受处理器和 OpenAPI 操作字段字典。额外信息会深度合并到生成的操作对象中。

## 自定义 Content-Type

通过继承 `HttpRequest` 覆盖文档中的请求 Content-Type：

```python
from typing import Any
from typing_extensions import Annotated
from baize.datastructures import ContentType
from kui.asgi import HttpRequest, FactoryClass, Kui

class MsgPackRequest(HttpRequest):
    async def data(self) -> Annotated[Any, ContentType("application/x-msgpack")]:
        body = await self.body
        return msgpack.unpackb(body)

app = Kui(factory_class=FactoryClass(http=MsgPackRequest))
```

## Schema 命名

当多个 Pydantic 模型共享相同类名（例如不同模块中的 `Item` 模型）时，Kuí 会自动为 Schema 名称添加路由路径前缀以避免冲突。
