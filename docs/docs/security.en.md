# Security

Kuí provides built-in authentication helpers that integrate with the dependency injection system and auto-generate OpenAPI security schemes.

## Bearer Token Authentication

Extract a Bearer token from the `Authorization` header:

```python
from typing_extensions import Annotated
from kui.asgi import Depends, bearer_auth

@app.router.http.get("/me")
async def me(token: Annotated[str, Depends(bearer_auth)]):
    user = decode_jwt(token)
    return {"user": user}
```

- Expects: `Authorization: Bearer <token>`
- Returns: the token string
- Raises: `HTTPException(401)` with `WWW-Authenticate: Bearer` if missing or invalid format
- OpenAPI: generates `BearerAuth` security scheme

## Basic Authentication

Extract username and password from HTTP Basic Auth:

```python
from kui.asgi import Depends, basic_auth

@app.router.http.get("/admin")
async def admin(
    credentials: Annotated[tuple[str, str], Depends(basic_auth)],
):
    username, password = credentials
    if not verify_password(username, password):
        raise HTTPException(403)
    return {"user": username}
```

- Expects: `Authorization: Basic <base64(username:password)>`
- Returns: `(username, password)` tuple
- Raises: `HTTPException(401)` with `WWW-Authenticate: Basic` if missing or invalid
- OpenAPI: generates `BasicAuth` security scheme

## API Key Authentication

Validate an API key from a header, query parameter, or cookie:

```python
from kui.asgi import Depends, api_key_auth_dependency

# From header
api_key = api_key_auth_dependency("X-API-Key", position="header")

@app.router.http.get("/data")
async def data(key: Annotated[str, Depends(api_key)]):
    return {"data": "secret"}

# From query parameter
api_key_query = api_key_auth_dependency("api_key", position="query")

# From cookie
api_key_cookie = api_key_auth_dependency("session", position="cookie")
```

- `position`: `"header"`, `"query"`, or `"cookie"`
- Returns: the API key string
- Raises: `HTTPException(401)` if the key is missing
- OpenAPI: generates `ApiKeyAuth` security scheme with the correct location

## OpenAPI Integration

All security dependencies auto-generate OpenAPI `securitySchemes` in the `components` section and `security` requirements on operations.

```python
from kui.asgi import Kui, OpenAPI, HttpRoute, Depends, bearer_auth

app = Kui(routes=[
    HttpRoute("/me", me),
])
app.router <<= "/docs" // OpenAPI(
    info={"title": "My API", "version": "1.0.0"},
).routes
```

The generated spec includes:

```json
{
    "components": {
        "securitySchemes": {
            "BearerAuth": {
                "type": "http",
                "scheme": "bearer"
            }
        }
    },
    "paths": {
        "/me": {
            "get": {
                "security": [{"BearerAuth": []}]
            }
        }
    }
}
```

## Custom Authentication

Create your own authentication dependency:

```python
from kui.asgi import Depends, Header, HTTPException

async def verify_api_token(
    authorization: Annotated[str, Header(alias="authorization")],
):
    if not authorization.startswith("Bearer "):
        raise HTTPException(401, headers={"WWW-Authenticate": "Bearer"})
    token = authorization[7:]
    user = await verify_and_decode(token)
    if not user:
        raise HTTPException(401)
    return user

@app.router.http.get("/protected")
async def protected(
    user: Annotated[User, Depends(verify_api_token)],
):
    return {"user": user.name}
```

Custom dependencies with `Header`/`Query`/`Cookie` parameters are auto-documented in OpenAPI but won't generate a `securitySchemes` entry. Use `describe_extra_docs` to add custom security schemes if needed.
