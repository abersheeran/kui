# Parameter Binding

Kuí extracts and validates request parameters automatically using `typing_extensions.Annotated` and Pydantic. The framework inspects handler signatures, extracts values from the request, validates them, and injects them as keyword arguments.

## Overview

```python
from typing_extensions import Annotated
from kui.asgi import Path, Query, Header, Cookie, Body

@app.router.http.get("/items/{item_id:int}")
async def get_item(
    item_id: Annotated[int, Path()],
    q: Annotated[str, Query(...)],                    # required
    limit: Annotated[int, Query(10)],                  # default = 10
    x_token: Annotated[str, Header(alias="x-token")],  # header (alias lowercased)
    session: Annotated[str, Cookie()] = "",             # optional with default
):
    ...
```

Each parameter location has its own annotation: `Path`, `Query`, `Header`, `Cookie`, `Body`.

## Path Parameters

Extract values from URL path segments:

```python
@app.router.http.get("/users/{user_id:int}")
async def get_user(user_id: Annotated[int, Path()]):
    return {"id": user_id}
```

Path parameters are always required. The type in the route pattern (`{user_id:int}`) performs initial parsing; the `Annotated[int, Path()]` annotation provides Pydantic validation.

## Query Parameters

Extract values from the URL query string:

```python
@app.router.http.get("/search")
async def search(
    q: Annotated[str, Query(...)],           # required (... = no default)
    page: Annotated[int, Query(1)],          # default = 1
    limit: Annotated[int, Query(10)],        # default = 10
):
    return {"q": q, "page": page, "limit": limit}
```

For multi-value query parameters (e.g., `?tag=a&tag=b`), use a list type:

```python
tags: Annotated[list[str], Query([])]
```

## Header Parameters

Extract values from HTTP headers:

```python
@app.router.http.get("/protected")
async def protected(
    x_token: Annotated[str, Header(alias="x-token")],
):
    return {"token": x_token}
```

!!! note
    Header aliases are automatically lowercased for case-insensitive matching. Use `alias` to match the actual header name format (e.g., `"x-token"` matches the `X-Token` header).

## Cookie Parameters

Extract values from cookies:

```python
@app.router.http.get("/me")
async def me(
    session_id: Annotated[str, Cookie(alias="session-id")] = "",
):
    return {"session": session_id}
```

## Body Parameters

Extract values from the request body (JSON or form data):

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

### Exclusive Body Mode

By default, multiple `Body()` parameters are merged into a single Pydantic model. Use `exclusive=True` to map the **entire** request body to one parameter:

```python
@app.router.http.post("/raw")
async def raw_body(data: Annotated[dict, Body(exclusive=True)]):
    return data
```

### Multiple Body Fields

Without `exclusive`, multiple body parameters form a combined model:

```python
@app.router.http.post("/update")
async def update(
    name: Annotated[str, Body(...)],
    age: Annotated[int, Body(...)],
):
    # Expects JSON: {"name": "Alice", "age": 30}
    return {"name": name, "age": age}
```

## File Upload

Use `UploadFile` for file uploads:

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

`UploadFile` attributes and methods:

| Attribute/Method | Description |
|---|---|
| `.filename` | Original filename |
| `.content_type` | MIME type |
| `.headers` | File part headers |
| `.file` | Underlying file object |
| `await .aread()` | Read file content |
| `await .awrite(data)` | Write data |
| `await .aseek(offset)` | Seek to position |
| `await .asave(path)` | Save to file path |
| `await .aclose()` | Close file |

!!! note
    In WSGI mode, use synchronous methods: `.read()`, `.write()`, `.seek()`, `.save()`, `.close()`.

When `UploadFile` is used, the OpenAPI schema automatically sets the content type to `multipart/form-data`.

## Field Options

All parameter functions (`Path`, `Query`, `Header`, `Cookie`, `Body`) accept standard Pydantic `Field` keyword arguments:

| Option | Description | Example |
|---|---|---|
| First positional | Default value (`...` = required) | `Query(...)`, `Query(10)` |
| `alias` | Alternative field name | `Header(alias="x-token")` |
| `title` | OpenAPI title | `Query(title="Search Query")` |
| `description` | OpenAPI description | `Query(description="Filter term")` |
| `ge`, `gt`, `le`, `lt` | Numeric constraints | `Query(ge=0, le=100)` |
| `min_length`, `max_length` | String length constraints | `Query(min_length=1)` |
| `pattern` | Regex pattern constraint | `Query(pattern=r"^\w+$")` |

```python
@app.router.http.get("/items")
async def list_items(
    page: Annotated[int, Query(1, ge=1, description="Page number")],
    size: Annotated[int, Query(20, ge=1, le=100, description="Page size")],
):
    ...
```

## Pydantic Model Support

Use Pydantic `BaseModel` for complex parameter structures:

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

Nested models are fully supported and generate proper OpenAPI schemas.

## Validation Errors

When parameter validation fails, the framework returns:

- **422 Unprocessable Entity** — for query, header, cookie, or body validation errors
- **404 Not Found** — for path parameter validation errors (e.g., `/users/abc` when `int` is expected)

The response body contains a JSON array of error details:

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

The `"in"` field indicates the parameter location (`"path"`, `"query"`, `"header"`, `"cookie"`, `"body"`).

See [Exception Handling](exceptions.md) for customizing error responses.
