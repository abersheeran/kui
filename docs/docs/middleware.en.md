# Middleware

A middleware is a function that wraps an endpoint handler. It receives the endpoint and returns a new handler:

```python
def my_middleware(endpoint):
    async def wrapper():
        # Before handler
        print("before")
        result = await endpoint()
        # After handler
        print("after")
        return result
    return wrapper
```

!!! warning
    Do **NOT** use `@functools.wraps` on middleware wrappers. The framework raises `RuntimeError` if it detects this, because `functools.wraps` copies attributes that interfere with parameter binding and OpenAPI generation.

## Applying Middleware

### Per-Route with `@` Operator

```python
from kui.asgi import HttpRoute, required_method, allow_cors

route = HttpRoute("/data", handler) @ required_method("GET") @ allow_cors()
app.router <<= route
```

Middleware is applied right-to-left: `allow_cors` wraps first, then `required_method`.

### Per-Route via Decorator Parameter

```python
@app.router.http.get("/data", middlewares=[my_middleware])
async def handler():
    ...
```

### Per-Routes Group

```python
from kui.asgi import Routes, HttpRoute

routes = Routes(
    HttpRoute("/a", handler_a),
    HttpRoute("/b", handler_b),
    http_middlewares=[auth_middleware, logging_middleware],
)
```

Or register with a decorator:

```python
routes = Routes()

@routes.http_middleware
def logging_middleware(endpoint):
    async def wrapper():
        print(f"Request received")
        return await endpoint()
    return wrapper

@routes.http.get("/")
async def handler():
    return "ok"
```

### App-Level

```python
app = Kui(
    http_middlewares=[logging_middleware, auth_middleware],
    socket_middlewares=[ws_auth_middleware],  # ASGI only
)
```

## Middleware with Parameters

Middleware wrappers can declare `Annotated` parameters for automatic request binding:

```python
from typing_extensions import Annotated
from kui.asgi import Header

def auth_middleware(endpoint):
    async def wrapper(
        authorization: Annotated[str, Header(alias="authorization")],
    ):
        if not verify_token(authorization):
            raise HTTPException(401)
        return await endpoint()
    return wrapper
```

These parameters are:

- Automatically extracted from the request
- Validated via Pydantic
- Included in OpenAPI documentation

## Middleware Execution Order

Middleware is applied in this order (outermost to innermost):

1. **App-level** middleware (`http_middlewares` on `Kui`)
2. **Routes group** middleware (`http_middlewares` on `Routes`)
3. **Per-route** middleware (via `@` operator or `middlewares=` parameter)

The handler runs last, at the innermost level.

## Built-in Middleware

### `required_method`

Restrict a handler to specific HTTP methods:

```python
from kui.asgi import required_method

route = HttpRoute("/data", handler) @ required_method("GET")
```

Returns `405 Method Not Allowed` for non-matching methods. Returns `200` for `OPTIONS` requests with an `Allow` header.

### `allow_cors`

Per-route CORS middleware:

```python
from kui.asgi import allow_cors

route = HttpRoute("/api", handler) @ allow_cors(
    allow_origins=[re.compile(r"https://example\.com")],
    allow_methods=["GET", "POST"],
    allow_headers=["Authorization"],
    max_age=600,
)
```

See [CORS](cors.md) for details.

## Example: Timing Middleware

```python
import time

def timing_middleware(endpoint):
    async def wrapper():
        start = time.monotonic()
        response = await endpoint()
        elapsed = time.monotonic() - start
        print(f"Request took {elapsed:.3f}s")
        return response
    return wrapper

app = Kui(http_middlewares=[timing_middleware])
```
