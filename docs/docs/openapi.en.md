# OpenAPI Documentation

Kuí auto-generates [OpenAPI 3.1.0](https://spec.openapis.org/oas/v3.1.0) documentation from your code — type annotations, docstrings, and route metadata.

## Setup

```python
from kui.asgi import Kui, OpenAPI

app = Kui()

openapi = OpenAPI(
    info={"title": "My API", "version": "1.0.0"},
    template_name="swagger",      # "swagger" | "redoc" | "rapidoc"
    security_schemes={},           # Optional: custom OpenAPI security schemes
)

# Mount at /docs
app.router <<= "/docs" // openapi.routes
```

This serves:

| Path | Description |
|---|---|
| `GET /docs/` | Interactive HTML UI |
| `GET /docs/json` | OpenAPI 3.1.0 JSON schema |
| `GET /docs/heartbeat` | SSE endpoint for hot reload |

### UI Options

| Template | Description |
|---|---|
| `"swagger"` | [Swagger UI](https://swagger.io/tools/swagger-ui/) — interactive, with "Try it out" |
| `"redoc"` | [ReDoc](https://redocly.github.io/redoc/) — clean, read-only documentation |
| `"rapidoc"` | [RapiDoc](https://rapidocweb.com/) — modern, customizable |

You can also provide a custom HTML template:

```python
openapi = OpenAPI(
    info={"title": "My API", "version": "1.0.0"},
    template="<html>...</html>",  # Custom HTML string
)
```

### Reload Mode

Set `reload=True` to regenerate the spec on each request (useful during development):

```python
openapi = OpenAPI(info={"title": "My API", "version": "1.0.0"}, reload=True)
```

## Auto-Generated Documentation

### From Docstrings

The handler's docstring generates `summary` and `description`:

```python
@app.router.http.get("/users")
async def list_users():
    """
    List all users

    Returns a paginated list of all registered users.
    Supports filtering by status and role.
    """
    return [...]
```

- First paragraph → `summary`
- Remaining text → `description`

### From Route Parameters

```python
@app.router.http.get("/users", summary="List users", description="...", tags=["Users"])
async def list_users():
    ...
```

### From Parameter Binding

Parameters declared with `Annotated` are automatically documented:

```python
@app.router.http.get("/users")
async def list_users(
    page: Annotated[int, Query(1, ge=1, description="Page number")],
    size: Annotated[int, Query(20, ge=1, le=100, description="Items per page")],
):
    ...
```

Generates OpenAPI `parameters` entries with type, location, default, constraints, and description.

### From Body Parameters

Pydantic models in `Body()` generate `requestBody` with JSON schema:

```python
class UserCreate(BaseModel):
    name: str
    email: str

@app.router.http.post("/users")
async def create_user(user: Annotated[UserCreate, Body(exclusive=True)]):
    ...
```

### From Dependencies

Parameters declared in dependency functions also appear in the docs:

```python
async def verify_token(token: Annotated[str, Header(alias="authorization")]):
    ...

@app.router.http.get("/me")
async def me(user: Annotated[User, Depends(verify_token)]):
    ...
```

The `authorization` header parameter appears in the OpenAPI spec for `/me`.

## Response Documentation

Document response types using return type annotations:

```python
from typing import Any
from typing_extensions import Annotated
from kui.asgi import JSONResponse

@app.router.http.get("/users")
async def list_users() -> Annotated[Any, JSONResponse[200, {}, list[UserModel]]]:
    return [...]
```

### Response Subscript Syntax

```python
# Status code only
JSONResponse[200]

# Status code + headers
JSONResponse[200, {"X-Request-Id": {"schema": {"type": "string"}}}]

# Status code + headers + body schema
JSONResponse[200, {}, UserModel]
```

Available response classes: `JSONResponse`, `HTMLResponse`, `PlainTextResponse`, `FileResponse`, `RedirectResponse`, `SendEventResponse`, `StreamResponse`.

### Multiple Response Types

List multiple response annotations inside a single `Annotated`:

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

## Tags

### On Individual Routes

```python
@app.router.http.get("/users", tags=["Users"])
async def list_users():
    ...
```

### On Route Groups

```python
routes = Routes(
    HttpRoute("/users", list_users),
    HttpRoute("/posts", list_posts),
    tags=["API"],
)
```

### Tag Descriptions and Paths

Configure tag descriptions and path mappings in the `OpenAPI` constructor:

```python
openapi = OpenAPI(
    info={"title": "My API", "version": "1.0.0"},
    tags={
        "Users": {"description": "User management endpoints"},
        "Posts": {
            "description": "Blog post endpoints",
            "paths": ["/posts", "/posts/{post_id}"],  # Auto-tag these paths
        },
    },
)
```

Each tag entry accepts:

- `description` (required) — Tag description for the OpenAPI spec
- `paths` (optional) — List of path strings; routes matching these paths are automatically tagged

## Security Schemes

Security dependencies (Bearer, Basic, API Key) are automatically documented:

```python
from kui.asgi import Depends, bearer_auth

@app.router.http.get("/me")
async def me(token: Annotated[str, Depends(bearer_auth)]):
    ...
```

This generates a `securitySchemes` entry in the OpenAPI `components` and a `security` requirement on the operation.

See [Security](security.md) for all authentication options.

## Extra Documentation

Use `describe_extra_docs` to supplement the auto-generated docs for an endpoint:

```python
from kui.openapi import describe_extra_docs

@app.router.http.get("/users")
async def list_users():
    ...

describe_extra_docs(list_users, {
    "responses": {
        "500": {"description": "Internal server error"},
    },
    "deprecated": True,
})
```

`describe_extra_docs(handler, info)` takes a handler and a dict of OpenAPI operation fields. The info is deep-merged into the generated operation object.

## Custom Content-Type

Override the documented request Content-Type by subclassing `HttpRequest`:

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

## Schema Naming

When multiple Pydantic models share the same class name (e.g., different `Item` models in different modules), Kuí automatically prefixes schema names with the route path to avoid conflicts.
