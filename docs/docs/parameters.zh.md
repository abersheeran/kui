# 参数绑定

Kuí 使用 `typing_extensions.Annotated` 和 Pydantic 自动提取和验证请求参数。框架检查处理器签名，从请求中提取值，进行验证，并作为关键字参数注入。

## 概览

```python
from typing_extensions import Annotated
from kui.asgi import Path, Query, Header, Cookie, Body

@app.router.http.get("/items/{item_id:int}")
async def get_item(
    item_id: Annotated[int, Path()],
    q: Annotated[str, Query(...)],                    # 必填
    limit: Annotated[int, Query(10)],                  # 默认值 = 10
    x_token: Annotated[str, Header(alias="x-token")],  # 头部（别名小写）
    session: Annotated[str, Cookie()] = "",             # 可选，带默认值
):
    ...
```

每个参数位置都有对应的注解：`Path`、`Query`、`Header`、`Cookie`、`Body`。

## 路径参数

从 URL 路径段中提取值：

```python
@app.router.http.get("/users/{user_id:int}")
async def get_user(user_id: Annotated[int, Path()]):
    return {"id": user_id}
```

路径参数始终必填。路由模式中的类型（`{user_id:int}`）进行初始解析；`Annotated[int, Path()]` 注解提供 Pydantic 验证。

## 查询参数

从 URL 查询字符串中提取值：

```python
@app.router.http.get("/search")
async def search(
    q: Annotated[str, Query(...)],           # 必填（... = 无默认值）
    page: Annotated[int, Query(1)],          # 默认值 = 1
    limit: Annotated[int, Query(10)],        # 默认值 = 10
):
    return {"q": q, "page": page, "limit": limit}
```

多值查询参数（如 `?tag=a&tag=b`）使用列表类型：

```python
tags: Annotated[list[str], Query([])]
```

## 头部参数

从 HTTP 头部提取值：

```python
@app.router.http.get("/protected")
async def protected(
    x_token: Annotated[str, Header(alias="x-token")],
):
    return {"token": x_token}
```

!!! note
    头部别名自动转为小写以进行大小写不敏感匹配。使用 `alias` 匹配实际的头部名称格式（例如 `"x-token"` 匹配 `X-Token` 头部）。

## Cookie 参数

从 Cookie 中提取值：

```python
@app.router.http.get("/me")
async def me(
    session_id: Annotated[str, Cookie(alias="session-id")] = "",
):
    return {"session": session_id}
```

## 请求体参数

从请求体提取值（JSON 或表单数据）：

```python
from pydantic import BaseModel

class CreateUser(BaseModel):
    name: str
    email: str
    age: int

@app.router.http.post("/users")
async def create_user(user: Annotated[CreateUser, Body(...)]):
    return user, 201
```

### 独占模式

默认情况下，多个 `Body()` 参数会合并为一个 Pydantic 模型。使用 `exclusive=True` 将**整个**请求体映射到一个参数：

```python
@app.router.http.post("/raw")
async def raw_body(data: Annotated[dict, Body(exclusive=True)]):
    return data
```

### 多个请求体字段

不使用 `exclusive` 时，多个 body 参数会组成一个合并模型：

```python
@app.router.http.post("/update")
async def update(
    name: Annotated[str, Body(...)],
    age: Annotated[int, Body(...)],
):
    # 期望 JSON：{"name": "Alice", "age": 30}
    return {"name": name, "age": age}
```

## 文件上传

使用 `UploadFile` 进行文件上传：

```python
from kui.asgi import UploadFile

@app.router.http.post("/upload")
async def upload(file: Annotated[UploadFile, Body(...)]):
    content = await file.aread()
    return {
        "filename": file.filename,
        "content_type": file.content_type,
        "size": len(content),
    }
```

`UploadFile` 属性和方法：

| 属性/方法 | 说明 |
|---|---|
| `.filename` | 原始文件名 |
| `.content_type` | MIME 类型 |
| `.headers` | 文件部分头部 |
| `.file` | 底层文件对象 |
| `await .aread()` | 读取文件内容 |
| `await .awrite(data)` | 写入数据 |
| `await .aseek(offset)` | 定位到指定位置 |
| `await .asave(path)` | 保存到文件路径 |
| `await .aclose()` | 关闭文件 |

!!! note
    WSGI 模式下使用同步方法：`.read()`、`.write()`、`.seek()`、`.save()`、`.close()`。

使用 `UploadFile` 时，OpenAPI Schema 会自动将内容类型设置为 `multipart/form-data`。

## 字段选项

所有参数函数（`Path`、`Query`、`Header`、`Cookie`、`Body`）接受标准 Pydantic `Field` 关键字参数：

| 选项 | 说明 | 示例 |
|---|---|---|
| 第一个位置参数 | 默认值（`...` = 必填） | `Query(...)`、`Query(10)` |
| `alias` | 替代字段名 | `Header(alias="x-token")` |
| `title` | OpenAPI 标题 | `Query(title="搜索词")` |
| `description` | OpenAPI 描述 | `Query(description="过滤条件")` |
| `ge`、`gt`、`le`、`lt` | 数值约束 | `Query(ge=0, le=100)` |
| `min_length`、`max_length` | 字符串长度约束 | `Query(min_length=1)` |
| `pattern` | 正则表达式约束 | `Query(pattern=r"^\w+$")` |

```python
@app.router.http.get("/items")
async def list_items(
    page: Annotated[int, Query(1, ge=1, description="页码")],
    size: Annotated[int, Query(20, ge=1, le=100, description="每页大小")],
):
    ...
```

## Pydantic 模型支持

使用 Pydantic `BaseModel` 处理复杂参数结构：

```python
from pydantic import BaseModel

class ItemCreate(BaseModel):
    name: str
    price: float
    tags: list[str] = []

@app.router.http.post("/items")
async def create_item(item: Annotated[ItemCreate, Body(exclusive=True)]):
    return item, 201
```

完全支持嵌套模型，并生成正确的 OpenAPI Schema。

## 验证错误

参数验证失败时，框架返回：

- **422 Unprocessable Entity** — 查询、头部、Cookie 或请求体验证错误
- **404 Not Found** — 路径参数验证错误（例如期望 `int` 时访问 `/users/abc`）

响应体包含 JSON 错误详情数组：

```json
[
    {
        "loc": ["page"],
        "msg": "Input should be a valid integer, unable to parse string as an integer",
        "type": "int_parsing",
        "in": "query"
    }
]
```

`"in"` 字段标识参数位置（`"path"`、`"query"`、`"header"`、`"cookie"`、`"body"`）。

自定义错误响应请参见[异常处理](exceptions.md)。
