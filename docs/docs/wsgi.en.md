# WSGI Mode

Kuí supports both ASGI and WSGI. The API is nearly identical — this page documents the differences.

## When to Use WSGI

- Your application is fully synchronous
- You don't need WebSocket or Lifespan events
- You want to use a mature WSGI server (Gunicorn, uWSGI, etc.)
- Your deployment environment requires WSGI

## Differences from ASGI

| Feature | ASGI | WSGI |
|---|---|---|
| Import | `from kui.asgi import ...` | `from kui.wsgi import ...` |
| Handlers | `async def handler():` | `def handler():` |
| Dependencies | `async def` or `def` | `def` only |
| Generator deps | `async def` generator | `def` generator |
| WebSocket | Yes (`SocketRoute`, `SocketView`) | Not available |
| Lifespan | Yes (`on_startup`, `on_shutdown`) | Not available |
| `socket_middlewares` | Yes | Not available |
| Server-Sent Events | `SendEventResponse` | `SendEventResponse` |
| Everything else | Same API | Same API |

## Quick Start

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

Run with:

```bash
gunicorn app:app
```

## WSGI Handler Examples

### Function Handler

```python
from kui.wsgi import request

@app.router.http.get("/users")
def list_users():
    return [{"id": 1, "name": "Alice"}]

@app.router.http.post("/users")
def create_user(user: Annotated[UserCreate, Body(exclusive=True)]):
    return user, 201
```

### Class-Based View

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

### Request Access

```python
from kui.wsgi import request

@app.router.http.get("/info")
def info():
    return {
        "method": request.method,
        "path": request.url.path,
    }
```

Body parsing is synchronous:

```python
body = request.body    # bytes (cached property)
data = request.json    # parsed JSON (cached property)
form = request.form    # parsed form data (cached property)
data = request.data()  # auto-detect format (method call)
```

!!! note
    `body`, `json`, and `form` are cached properties (no parentheses). Only `data()` is a method call.

### Dependency Injection

```python
from kui.wsgi import Depends

def get_db():
    return database.connect()

# Generator dependency with cleanup
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

### File Upload

```python
from kui.wsgi import UploadFile

@app.router.http.post("/upload")
def upload(file: Annotated[UploadFile, Body(...)]):
    content = file.read()  # Synchronous read
    return {"filename": file.filename, "size": len(content)}
```

### Custom Response Converter

```python
app = Kui(
    response_converters={
        MyType: lambda obj, status=200, headers=None: JSONResponse(
            obj.to_dict(), status, headers
        ),
    }
)
```

## Application Configuration

WSGI `Kui` accepts the same parameters as ASGI, except:

- No `on_startup` / `on_shutdown`
- No `socket_middlewares`

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

## Available Exports

WSGI exports the same symbols as ASGI, minus WebSocket-related ones:

- No: `WebSocket`, `websocket`, `websocket_var`, `SocketView`
- `SocketRoute` is exported but has no practical use in WSGI (no WebSocket server support)
- Everything else: `Kui`, `OpenAPI`, `HttpRoute`, `Routes`, `MultimethodRoutes`, `HttpView`, `Path`, `Query`, `Header`, `Cookie`, `Body`, `Depends`, `UploadFile`, `request`, `HTTPException`, `allow_cors`, `required_method`, `bearer_auth`, `basic_auth`, `api_key_auth_dependency`, all response classes, etc.
