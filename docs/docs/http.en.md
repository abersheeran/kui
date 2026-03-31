# HTTP

## Handlers

### Function Handlers

The simplest way to handle HTTP requests:

```python
from kui.asgi import Kui

app = Kui()

@app.router.http.get("/")
async def homepage():
    return {"message": "Hello!"}
```

Handlers can return various types that are automatically converted to responses (see [Response Conversion](#response-conversion) below).

### Class-Based Views (HttpView)

For endpoints that handle multiple HTTP methods:

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

Supported methods: `get`, `post`, `put`, `patch`, `delete`, `head`, `options`, `trace`.

- `OPTIONS` is auto-generated with an `Allow` header if not defined.
- Unsupported methods return `405 Method Not Allowed`.
- Each method is a `@classmethod` (ASGI: `async`, WSGI: sync).

### Method Restriction

Restrict a function handler to specific HTTP methods:

```python
from kui.asgi import HttpRoute, required_method

app.router <<= HttpRoute("/data", handler) @ required_method("GET")
```

Returns `405` for non-matching methods, `200` for `OPTIONS`.

## Request Object

Access the current request via the `request` context variable — no parameter needed:

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

### Request Attributes

| Attribute | Type | Description |
|---|---|---|
| `request.method` | `str` | HTTP method (`GET`, `POST`, etc.) |
| `request.url` | `URL` | Full URL object (`.path`, `.query`, `.scheme`, `.host`) |
| `request.headers` | `Headers` | Case-insensitive header mapping |
| `request.query_params` | `QueryParams` | Query string parameters |
| `request.path_params` | `dict` | Extracted path parameters |
| `request.cookies` | `dict` | Cookie mapping |
| `request.client` | `Address` | Client address (`.host`, `.port`) |
| `request.state` | `State` | Per-request mutable state |
| `request.app` | `Kui` | The application instance |

### Request Body

```python
# Raw bytes (cached property, not a method call)
body = await request.body

# JSON (cached property)
data = await request.json

# Form data (cached property)
form = await request.form

# Auto-detect format based on Content-Type (method call)
data = await request.data()
```

!!! note
    In ASGI mode, `body`, `json`, and `form` are awaitable cached properties (use `await request.body`, not `await request.body()`). Only `data()` is a method call.

!!! tip
    Prefer [Parameter Binding](parameters.md) over manual body parsing. It provides automatic validation and OpenAPI documentation.

### File Upload

```python
form = await request.form
upload = form["file"]  # UploadFile object
content = await upload.aread()
filename = upload.filename
content_type = upload.content_type
```

### Per-Request State

Store request-scoped data via `request.state`:

```python
# Write
request.state.user = current_user

# Read
name = request.state.user.name

# Delete
del request.state.user
```

`State` supports both sync and async context managers for thread-safe access:

```python
async with request.state as state:
    state.counter = state.get("counter", 0) + 1
```

### Background Tasks

Queue tasks that run after the response is sent:

```python
@app.router.http.post("/notify")
async def notify():
    request.background_tasks.append(send_email, to="user@example.com")
    return {"status": "queued"}
```

See [Background Tasks](background-tasks.md) for details.

## Response Types

### Automatic Response Conversion

Handlers can return plain Python values — the framework converts them automatically:

| Return Type | Converted To |
|---|---|
| `str`, `bytes` | `PlainTextResponse` |
| `dict`, `list` | `JSONResponse` |
| `pydantic.BaseModel` | `JSONResponse` |
| `pathlib.PurePath` | `FileResponse` |
| `baize.datastructures.URL` | `RedirectResponse` |
| `AsyncGenerator` (ASGI) / `Generator` (WSGI) | `SendEventResponse` |
| `HttpResponse` subclass | Used as-is |

### Status Code and Headers via Tuple

Return a tuple to set status code and headers:

```python
# (body, status_code)
return {"id": 1}, 201

# (body, status_code, headers)
return {"id": 1}, 201, {"X-Custom": "value"}
```

### Response Classes

For full control, use response classes directly:

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

Supports `Range` requests (status 206) automatically.

#### StreamResponse

```python
async def stream():
    for chunk in data_chunks:
        yield chunk

return StreamResponse(stream())
```

#### SendEventResponse (Server-Sent Events)

```python
async def events():
    for i in range(10):
        yield {"id": i, "data": "hello"}
        await asyncio.sleep(1)

return SendEventResponse(events())
```

Or return an async generator directly from the handler — it auto-converts:

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

Requires Jinja2 templates configured. See [Templates](templates.md).

### HttpResponse Base

All response classes inherit from `HttpResponse`, which provides:

```python
response = HttpResponse(content=b"data", status_code=200)
response.headers["X-Custom"] = "value"
response.set_cookie("session", "abc123", max_age=3600, httponly=True)
response.delete_cookie("old_cookie")
```

### Custom Response Converters

Register custom type-to-response converters:

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

### Active Conversion

Use `convert_response(value)` to explicitly trigger response conversion outside normal handler return:

```python
from kui.asgi import convert_response

response = convert_response({"key": "value"})
```

## OpenAPI Response Documentation

Document response types for OpenAPI using return type annotations:

```python
from typing import Any
from typing_extensions import Annotated

@app.router.http.get("/users")
async def list_users() -> Annotated[Any, JSONResponse[200, {}, list[UserModel]]]:
    return [...]
```

Response class subscript syntax:

```python
# Status only
JSONResponse[200]

# Status + headers
JSONResponse[200, {"X-Custom": {"schema": {"type": "string"}}}]

# Status + headers + body schema
JSONResponse[200, {}, UserModel]
```

Available for: `JSONResponse`, `HTMLResponse`, `PlainTextResponse`, `FileResponse`, `RedirectResponse`, `SendEventResponse`, `StreamResponse`.

See [OpenAPI Documentation](openapi.md) for more.
