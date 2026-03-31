# 异常处理

## HTTPException

抛出 `HTTPException` 返回 HTTP 错误响应：

```python
from kui.asgi import HTTPException

@app.router.http.get("/items/{item_id:int}")
async def get_item(item_id: Annotated[int, Path()]):
    item = db.get(item_id)
    if not item:
        raise HTTPException(404)
    return item
```

带自定义内容和头部：

```python
raise HTTPException(
    403,
    content="Access denied",
    headers={"X-Reason": "insufficient-permissions"},
)
```

## 自定义异常处理器

为特定状态码或异常类型注册处理器：

### 状态码处理器

```python
@app.exception_handler(404)
async def not_found(exc):
    return {"error": "not found"}, 404

@app.exception_handler(500)
async def server_error(exc):
    return {"error": "internal server error"}, 500
```

### 异常类型处理器

```python
@app.exception_handler(ValueError)
async def value_error(exc):
    return {"error": str(exc)}, 400

@app.exception_handler(PermissionError)
async def permission_error(exc):
    return {"error": "forbidden"}, 403
```

异常类型处理器使用 MRO（方法解析顺序）查找——基类异常的处理器也会捕获子类。

### 通过构造函数注册

```python
app = Kui(
    exception_handlers={
        404: not_found_handler,
        ValueError: value_error_handler,
    }
)
```

## 验证错误

当[参数绑定](parameters.md)验证失败时，框架抛出 `RequestValidationError`：

- **路径参数**验证错误 → `404 Not Found`
- **查询/头部/Cookie/请求体**验证错误 → `422 Unprocessable Entity`

默认 422 响应体：

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

`"in"` 字段标识参数位置：`"path"`、`"query"`、`"header"`、`"cookie"` 或 `"body"`。

### 自定义验证错误处理器

```python
from kui.exceptions import RequestValidationError

@app.exception_handler(RequestValidationError)
async def validation_error(exc: RequestValidationError):
    return {
        "message": "Invalid request parameters",
        "details": exc.errors(),
    }, 422
```

`RequestValidationError` 提供：

| 方法/属性 | 说明 |
|---|---|
| `.errors()` | 包含 `loc`、`msg`、`type`、`in` 字段的错误字典列表 |
| `.json()` | 错误的 JSON 字符串 |
| `.in_` | 参数位置：`"path"`、`"query"`、`"header"`、`"cookie"`、`"body"` |

## 异常处理器执行

异常处理器包装端点处理器。当异常发生时：

1. 对于 `HTTPException`，框架首先检查状态码处理器（`_status_handlers`）
2. 如果状态码处理器未匹配，则查找异常类型处理器（沿 MRO 链查找）
3. 如果没有匹配的处理器，异常传播到 ASGI/WSGI 服务器

异常处理器接收异常作为唯一参数，应返回一个响应（或可转换为响应的值）。
