---
name: kui-framework
description: Guide for building web applications with the Kui framework. Use when writing Kui ASGI/WSGI handlers, defining routes, binding parameters, configuring OpenAPI docs, or working with middleware/dependency injection.
user-invocable: true
---

# Kui Web Framework Guide

Kui is a Python web framework supporting both ASGI (async) and WSGI (sync). It provides type-safe parameter binding via `Annotated`, dependency injection, OpenAPI documentation generation, class-based views, and middleware composition.

ASGI imports: `from kui.asgi import ...`
WSGI imports: `from kui.wsgi import ...`

The two modules expose nearly identical APIs; ASGI handlers are `async def`, WSGI handlers are plain `def`. All examples below use ASGI unless noted.

## 1. Application

```python
from kui.asgi import Kui, OpenAPI

app = Kui(
    routes=[],                  # Initial routes
    http_middlewares=[],         # App-level HTTP middleware
    socket_middlewares=[],       # App-level WebSocket middleware (ASGI only)
    cors_config=None,           # Optional CORSConfig dict
    exception_handlers={},      # {status_or_exc_type: handler}
    on_startup=[], on_shutdown=[],  # Lifespan callbacks (ASGI only)
    templates=None,             # Optional Jinja2Templates instance
    response_converters={},     # {type: converter_func}
    json_encoder={},            # {type: serializer_func}
)
```

`app` is a standard ASGI callable (`async def __call__(scope, receive, send)`).
For WSGI it is a standard `def __call__(environ, start_response)`.

### Shared state

```python
app.state.db = create_pool()   # Set once; ImmutableAttribute prevents reassignment
```

## 2. Routing

### 2.1 Decorator style (most common)

```python
@app.router.http.get("/users/{user_id:int}")
async def get_user(user_id: Annotated[int, Path()]):
    return {"id": user_id}

@app.router.http.post("/users")
async def create_user(body: Annotated[UserCreate, Body()]):
    return body, 201

# Any HTTP method
@app.router.http("/health")
async def health():
    return "ok"
```

Available method shortcuts: `.get()`, `.post()`, `.put()`, `.patch()`, `.delete()`.

Decorator parameters: `path`, `name=`, `middlewares=[]`, `summary=`, `description=`, `tags=`.

### 2.2 Route objects with `<<` operator

```python
from kui.asgi import HttpRoute, SocketRoute

app.router <<= HttpRoute("/", homepage)
app.router <<= SocketRoute("/ws", ws_handler)

# Chain multiple
app.router <<= (
    app.router
    << HttpRoute("/a", handler_a)
    << HttpRoute("/b", handler_b)
)
```

### 2.3 Routes container with prefix

```python
from kui.asgi import Routes, HttpRoute

api_routes = Routes(
    HttpRoute("/users", list_users),
    HttpRoute("/posts", list_posts),
    namespace="api",           # Prefixes route names
    tags=["API"],              # OpenAPI tags for all routes
    http_middlewares=[auth_mw],
)

# Prefix with // operator
app.router <<= "/api/v1" // api_routes
```

### 2.4 Reverse URL lookup

```python
app.router.url_for("route-name") # "/path"
app.router.url_for("user", {"id": 42}) # "/users/42"
```

### 2.5 Route middleware via `@` operator

```python
from kui.asgi import HttpRoute, required_method, allow_cors

route = HttpRoute("/data", handler) @ required_method("GET") @ allow_cors()
app.router <<= route
```

### 2.6 Path parameters

Supported converters: `{name}` (string), `{name:int}`, `{name:decimal}`, `{name:date}`, `{name:uuid}`, `{name:any}` (rest-of-path). `str` cannot match `/`; use `any` for rest-of-path (must be at the end).

### 2.7 WebSocket routing (ASGI only)

```python
@app.router.websocket("/ws")
async def ws_handler():
    await websocket.accept()
    data = await websocket.receive_json()
    await websocket.send_json({"echo": data})
    await websocket.close()
```

## 3. Parameter Binding

All parameter bindings use `typing_extensions.Annotated`. The framework inspects the handler signature, extracts and validates parameters via Pydantic, and injects them as keyword arguments.

```python
from typing_extensions import Annotated
from kui.asgi import Path, Query, Header, Cookie, Body

@app.router.http.get("/items/{item_id:int}")
async def get_item(
    item_id: Annotated[int, Path()],
    q: Annotated[str, Query(...)],                  # required query param
    limit: Annotated[int, Query(10)],                # default value
    x_token: Annotated[str, Header(alias="x-token")],  # header (alias lowercased)
    session: Annotated[str, Cookie()] = "",           # optional cookie
):
    ...
```

### Request body

```python
from pydantic import BaseModel

class Item(BaseModel):
    name: str
    price: float

@app.router.http.post("/items")
async def create_item(item: Annotated[Item, Body(...)]):
    return item

# Exclusive body: entire JSON body maps to one parameter
@app.router.http.post("/raw")
async def raw_body(data: Annotated[dict, Body(exclusive=True)]):
    return data
```

### Field options

`Path()`, `Query()`, `Header()`, `Cookie()`, `Body()` all accept standard Pydantic Field kwargs: `default`, `default_factory`, `alias`, `title`, `description`, plus any validation kwargs (`ge`, `le`, `min_length`, `max_length`, `pattern`, etc.).

### File upload

```python
from kui.asgi import UploadFile, Body

@app.router.http.post("/upload")
async def upload(file: Annotated[UploadFile, Body(...)]):
    return {"filename": file.filename, "content": file.read().decode()}
```

`UploadFile` attributes: `filename`, `content_type`, `headers`, `file`.
Methods: `awrite`, `aread`, `aseek`, `asave`, `aclose`.

## 4. Dependency Injection

```python
from kui.asgi import Depends

# Simple dependency
async def get_db():
    return db_pool.acquire()

# Generator dependency (with cleanup)
async def get_connection():
    conn = await db_pool.acquire()
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

- `cache=True` (default): result cached per request; same dependency injected once even if declared multiple times.
- `cache=False`: called fresh each time.
- Dependencies can declare their own `Annotated` parameters (nested injection).
- Both sync and async dependencies work. Generators and async generators are supported for setup/teardown.

## 5. Class-Based Views

### HttpView

```python
from kui.asgi import HttpView

@app.router.http("/users")
class UserView(HttpView):
    @classmethod
    async def get(cls):
        return [{"id": 1}]

    @classmethod
    async def post(cls):
        return {"created": True}, 201
```

Supported methods: `get`, `post`, `put`, `patch`, `delete`, `head`, `options`, `trace`.
`OPTIONS` auto-generated if not defined. Returns 405 for unsupported methods.

### SocketView (ASGI only)

```python
from kui.asgi import SocketView, websocket

@app.router.websocket("/chat")
class Chat(SocketView):
    encoding = "json"  # "text", "bytes", "json", "anystr"

    async def on_connect(self):
        await websocket.accept()

    async def on_receive(self, data):
        await websocket.send_json({"echo": data})

    async def on_disconnect(self, close_code: int):
        await websocket.close(code=close_code)
```

### MultimethodRoutes

Merge multiple single-method handlers for the same path into one class-based view automatically:

```python
from kui.asgi import MultimethodRoutes as Routes, HttpView

routes = Routes(base_class=HttpView)

@routes.http.get("/users")
async def list_users():
    return []

@routes.http.post("/users")
async def create_user():
    return {}, 201
```

## 6. Middleware

A middleware is a function `(endpoint) -> new_endpoint`:

```python
def logging_middleware(endpoint):
    async def wrapper():
        print("before")
        result = await endpoint()
        print("after")
        return result
    return wrapper
```

**Important**: Do NOT use `@functools.wraps` on middleware wrappers. The framework raises `RuntimeError` if it detects this.

### Apply middleware

```python
# Per-route via decorator parameter
@app.router.http.get("/", middlewares=[logging_middleware])
async def handler(): ...

# Per-route via @ operator
app.router <<= HttpRoute("/", handler) @ logging_middleware

# Per-Routes group
routes = Routes(..., http_middlewares=[logging_middleware])

# App-level
app = Kui(http_middlewares=[logging_middleware])

# Via Routes decorator
@routes.http_middleware
def mw(endpoint):
    async def wrapper():
        return await endpoint()
    return wrapper
```

Middleware can declare its own `Annotated` parameters for automatic binding:

```python
def auth_middleware(endpoint):
    async def wrapper(token: Annotated[str, Header(alias="authorization")]):
        verify(token)
        return await endpoint()
    return wrapper
```

## 7. Response Types

Handlers can return any of these types; the framework auto-converts:

| Return type | Converted to |
|---|---|
| `str`, `bytes` | `PlainTextResponse` |
| `dict`, `list` | `JSONResponse` |
| `BaseModel` | `JSONResponse` |
| `PurePath` | `FileResponse` |
| `URL` | `RedirectResponse` |
| `AsyncGenerator` (ASGI) / `Generator` (WSGI) | `SendEventResponse` |
| `HttpResponse` subclass | Used as-is |
| `(body, status)` or `(body, status, headers)` tuple | Converted via `response_converter` |

### OpenAPI response documentation

Use return type annotations:

```python
@app.router.http.get("/")
async def handler() -> Annotated[Any, JSONResponse[200, {}, UserModel]]:
    ...

# Status-only: JSONResponse[200]
# Status + headers: JSONResponse[200, {"X-Custom": {"schema": {"type": "string"}}}]
# Status + headers + body schema: JSONResponse[200, {}, UserModel]
```

Available: `JSONResponse`, `HTMLResponse`, `PlainTextResponse`, `FileResponse`, `RedirectResponse`, `SendEventResponse`, `StreamResponse`.

### Server-sent events

```python
@app.router.http.get("/events")
async def events():
    async def generate():
        for i in range(10):
            yield {"id": i, "data": "hello"}
            await asyncio.sleep(1)
    return generate()
```

### Custom response converters

```python
from dataclasses import dataclass

@dataclass
class Error:
    code: int
    message: str

app = Kui(
    response_converters={
        Error: lambda e, status=400, headers=None: JSONResponse(
            {"code": e.code, "message": e.message}, status, headers
        ),
    }
)
```

### Active conversion

Use `convert_response(value)` to explicitly trigger the response converter pipeline outside of normal handler return flow.

## 8. Request & WebSocket Objects

Access via context variables (no parameter needed):

```python
from kui.asgi import request, websocket

@app.router.http.get("/")
async def handler():
    request.method         # "GET"
    request.url            # Full URL object
    request.headers        # Headers mapping
    request.cookies        # Cookies dict
    request.path_params    # Extracted path params
    request.query_params   # Query params
    request.state          # Per-request State dict
    request.app            # The Kui instance
    await request.json     # Parse JSON body (cached property, no parentheses)
    await request.form     # Parse form body (cached property, no parentheses)
    await request.data()   # Auto-detect body format (method call)
```

### Per-request state

```python
request.state.user = current_user     # write
name = request.state.user.name        # read
del request.state.user                # delete
```

WebSocket methods (ASGI only):

```python
await websocket.accept()
await websocket.receive_text() / .receive_bytes() / .receive_json()
await websocket.send_text(s) / .send_bytes(b) / .send_json(obj)
await websocket.close(code=1000)
```

## 9. OpenAPI Documentation

```python
from kui.asgi import OpenAPI, Routes

openapi = OpenAPI(
    info={"title": "My API", "version": "1.0.0"},
    template_name="swagger",  # "swagger" | "redoc" | "rapidoc"
    reload=True,
)
app.router <<= "/docs" // openapi.routes
```

Serves:
- `GET /docs/` -- Interactive HTML UI
- `GET /docs/json` -- OpenAPI 3.1.0 JSON schema
- `GET /docs/heartbeat` -- SSE for hot reload

Documentation is auto-generated from:
- Handler docstrings (first paragraph = summary, rest = description)
- `summary=`, `description=`, `tags=` parameters on routes
- `Annotated` parameter types (Path, Query, Header, Cookie, Body)
- Return type annotations with response classes
- Dependency functions

### Extra documentation

Use `describe_extra_docs` to supplement OpenAPI docs for a specific endpoint. The descriptions will be merged into the generated documentation.

### Custom Content-Type

Override `HttpRequest.data()` with a `ContentType` annotation to change the documented request Content-Type:

```python
from typing import Any
from typing_extensions import Annotated
from baize.datastructures import ContentType
from kui.asgi import HttpRequest, FactoryClass, Kui

class MsgPackRequest(HttpRequest):
    async def data(self) -> Annotated[Any, ContentType("application/x-msgpack")]:
        ...

app = Kui(factory_class=FactoryClass(http=MsgPackRequest))
```

## 10. Exception Handling

```python
from kui.asgi import HTTPException

# Raise in handlers
raise HTTPException(404)
raise HTTPException(403, content="Forbidden", headers={"X-Reason": "auth"})

# Register handlers
@app.exception_handler(404)
async def not_found(exc):
    return {"error": "not found"}, 404

@app.exception_handler(ValueError)
async def value_error(exc):
    return {"error": str(exc)}, 400
```

Validation errors return 422 by default. Path validation errors return 404.

## 11. Authentication

```python
from kui.asgi import Depends, bearer_auth, basic_auth, api_key_auth_dependency

# Bearer token: Authorization: Bearer <token>
@app.router.http.get("/me")
async def me(token: Annotated[str, Depends(bearer_auth)]):
    return decode_jwt(token)

# Basic auth: Authorization: Basic <base64>
@app.router.http.get("/admin")
async def admin(creds: Annotated[tuple[str, str], Depends(basic_auth)]):
    username, password = creds
    ...

# API key from header/query/cookie
api_key = api_key_auth_dependency("X-API-Key", position="header")

@app.router.http.get("/data")
async def data(key: Annotated[str, Depends(api_key)]):
    ...
```

All raise `HTTPException(401)` with appropriate `WWW-Authenticate` headers when auth fails. OpenAPI security schemes are auto-documented.

## 12. CORS

```python
import re
from kui.asgi import allow_cors, Kui

# App-level
app = Kui(cors_config={
    "allow_origins": [re.compile(r"https://example\.com")],
    "allow_methods": ["GET", "POST"],
    "allow_headers": [],
    "expose_headers": [],
    "allow_credentials": False,
    "max_age": 600,
})

# Per-route
cors = allow_cors(allow_origins=[re.compile(".*")])
app.router <<= HttpRoute("/api", handler) @ cors
```

## 13. Lifespan (ASGI only)

Pass an async generator function to `Kui(lifespan=...)`. Code before `yield` runs on startup; code after `yield` runs on shutdown:

```python
async def lifespan(app: Kui):
    app.state.pool = await create_pool()
    yield
    await app.state.pool.close()

app = Kui(lifespan=lifespan)
```

`on_startup`/`on_shutdown` and `asynccontextmanager_lifespan` are deprecated.

## 14. Background Tasks

```python
from kui.asgi import request

@app.router.http.post("/notify")
async def notify():
    request.background_tasks.append(send_email, to="user@example.com")
    return {"status": "queued"}

async def send_email(to: str):
    ...
```

Background tasks run after the response is sent.

## 15. Templates (Jinja2)

```python
from kui.asgi import Jinja2Templates, TemplateResponse, request

templates = Jinja2Templates("templates")
app = Kui(templates=templates)

@app.router.http.get("/")
async def homepage():
    return TemplateResponse("index.html", {"request": request, "name": "World"})
```

## 16. Advanced

### Custom factory classes

```python
from kui.asgi import Kui, FactoryClass, HttpRequest, WebSocket

class CustomRequest(HttpRequest): ...
class CustomWS(WebSocket): ...

app = Kui(factory_class=FactoryClass(http=CustomRequest, websocket=CustomWS))
```

### Custom JSON encoder

```python
from datetime import datetime
app = Kui(json_encoder={datetime: lambda dt: dt.isoformat()})
```

### `app.should_exit`

Set `app.should_exit = True` to signal graceful shutdown (requires server support).

## Complete Example

```python
import asyncio
from pathlib import Path as FilePath
from typing_extensions import Annotated

from kui.asgi import (
    Kui, OpenAPI, HttpRoute, SocketRoute,
    Path, Query, Body, Depends,
    HTTPException, HttpView,
    allow_cors, required_method, websocket,
)
from pydantic import BaseModel

class Item(BaseModel):
    name: str
    price: float

items_db: list[Item] = []

async def get_items_db():
    return items_db

app = Kui(
    routes=[
        HttpRoute("/", lambda: "Welcome to Kui!"),
    ],
    http_middlewares=[allow_cors()],
)

@app.router.http.get("/items")
async def list_items(
    skip: Annotated[int, Query(0)],
    limit: Annotated[int, Query(10)],
    db: Annotated[list, Depends(get_items_db)],
):
    return db[skip:skip + limit]

@app.router.http.post("/items")
async def create_item(
    item: Annotated[Item, Body(exclusive=True)],
    db: Annotated[list, Depends(get_items_db)],
):
    db.append(item)
    return item, 201

app.router <<= "/docs" // OpenAPI(template_name="swagger").routes
```

