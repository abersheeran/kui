# Routing

Kuí uses a **Radix Tree** (compressed prefix tree) for fast route matching.

## Route Registration

### Decorator Style

The most common way to register routes:

```python
from kui.asgi import Kui

app = Kui()

# Any HTTP method
@app.router.http("/health")
async def health():
    return "ok"

# Specific methods
@app.router.http.get("/users")
async def list_users():
    return []

@app.router.http.post("/users")
async def create_user():
    return {}, 201
```

Available method shortcuts: `.get()`, `.post()`, `.put()`, `.patch()`, `.delete()`.

Decorator parameters:

| Parameter | Type | Description |
|---|---|---|
| `path` | `str` | URL path pattern |
| `name` | `str` | Route name for URL generation |
| `middlewares` | `list` | Route-level middleware list |
| `summary` | `str` | OpenAPI operation summary |
| `description` | `str` | OpenAPI operation description |
| `tags` | `list[str]` | OpenAPI tags |

### Route Objects with `<<` Operator

```python
from kui.asgi import HttpRoute, SocketRoute

app.router <<= HttpRoute("/", homepage)
app.router <<= SocketRoute("/ws", ws_handler)

# Chain multiple routes
app.router <<= (
    app.router
    << HttpRoute("/a", handler_a)
    << HttpRoute("/b", handler_b)
)
```

`HttpRoute` accepts: `path`, `endpoint`, `name`, `summary`, `description`, `tags`.

### Routes Container

Group routes together with shared configuration:

```python
from kui.asgi import Routes, HttpRoute

api_routes = Routes(
    HttpRoute("/users", list_users),
    HttpRoute("/posts", list_posts),
    namespace="api",              # Prefixes route names
    tags=["API"],                 # OpenAPI tags for all routes
    http_middlewares=[auth_mw],   # Shared middleware
)
```

`Routes` supports `<<` and `+` operators:

```python
routes = Routes(HttpRoute("/a", a))
routes <<= HttpRoute("/b", b)

combined = routes_a + routes_b
```

Routes also support slicing: `routes[1:3]`.

## Path Parameters

Path parameters are declared with `{name}` or `{name:type}` syntax:

| Type | Syntax | Matches | Example |
|---|---|---|---|
| `str` (default) | `{name}` | Any string except `/` | `/users/alice` |
| `int` | `{name:int}` | Integer digits | `/users/42` |
| `decimal` | `{name:decimal}` | Decimal number | `/price/19.99` |
| `date` | `{name:date}` | Date string | `/events/2024-01-15` |
| `uuid` | `{name:uuid}` | UUID string | `/items/550e8400-...` |
| `any` | `{name:any}` | Anything including `/` | `/files/path/to/file.txt` |

!!! note
    `{name:any}` must be at the end of the path. Static routes take precedence over dynamic routes (e.g., `/users/me` matches before `/users/{id}`).

```python
@app.router.http.get("/users/{user_id:int}")
async def get_user(user_id: Annotated[int, Path()]):
    return {"id": user_id}

@app.router.http.get("/files/{filepath:any}")
async def get_file(filepath: Annotated[str, Path()]):
    return FilePath(filepath)
```

## Common Prefix with `//` Operator

Add a shared prefix to a group of routes:

```python
from kui.asgi import Routes, HttpRoute

api = Routes(
    HttpRoute("/users", list_users),
    HttpRoute("/posts", list_posts),
)

# All routes prefixed with /api/v1
app.router <<= "/api/v1" // api
# Results: /api/v1/users, /api/v1/posts
```

This also works with OpenAPI routes:

```python
from kui.asgi import OpenAPI

app.router <<= "/docs" // OpenAPI(template_name="swagger").routes
```

## Reverse URL Lookup

Generate URLs from route names:

```python
app.router <<= HttpRoute("/users/{user_id:int}", get_user, name="user-detail")

url = app.router.url_for("user-detail", {"user_id": 42})
# Returns: "/users/42"
```

Inside a handler, use `request.url_for()`:

```python
from kui.asgi import request

@app.router.http.get("/")
async def homepage():
    user_url = request.url_for("user-detail", {"user_id": 1})
    return {"user_url": str(user_url)}
```

## Route Middleware

Apply middleware to individual routes using the `@` operator:

```python
from kui.asgi import HttpRoute, required_method, allow_cors

route = HttpRoute("/data", handler) @ required_method("GET") @ allow_cors()
app.router <<= route
```

Or pass middleware in the decorator:

```python
@app.router.http.get("/data", middlewares=[allow_cors()])
async def handler():
    ...
```

See [Middleware](middleware.md) for details on writing and applying middleware.

## MultimethodRoutes

Merge multiple single-method handlers for the same path into one view automatically:

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

This is equivalent to writing a class-based `HttpView` but allows you to keep handlers as separate functions. Internally, they are merged into a single view class.

## WebSocket Routing

ASGI only. Register WebSocket handlers:

```python
@app.router.websocket("/ws")
async def ws_handler():
    await websocket.accept()
    data = await websocket.receive_json()
    await websocket.send_json({"echo": data})
    await websocket.close()
```

Or with route objects:

```python
app.router <<= SocketRoute("/ws", ws_handler)
```

See [WebSocket](websocket.md) for full documentation.

## CLI: Display Routes

View all registered routes from the command line:

```bash
python -m kui.routing your_module:app
```
