# 安全

Kuí 提供内置的认证辅助工具，与依赖注入系统集成并自动生成 OpenAPI 安全方案。

## Bearer Token 认证

从 `Authorization` 头部提取 Bearer token：

```python
from typing_extensions import Annotated
from kui.asgi import Depends, bearer_auth

@app.router.http.get("/me")
async def me(token: Annotated[str, Depends(bearer_auth)]):
    user = decode_jwt(token)
    return {"user": user}
```

- 期望：`Authorization: Bearer <token>`
- 返回：token 字符串
- 失败时抛出：`HTTPException(401)` 并带有 `WWW-Authenticate: Bearer`
- OpenAPI：生成 `BearerAuth` 安全方案

## Basic 认证

从 HTTP Basic Auth 中提取用户名和密码：

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

- 期望：`Authorization: Basic <base64(username:password)>`
- 返回：`(username, password)` 元组
- 失败时抛出：`HTTPException(401)` 并带有 `WWW-Authenticate: Basic`
- OpenAPI：生成 `BasicAuth` 安全方案

## API Key 认证

从头部、查询参数或 Cookie 中验证 API Key：

```python
from kui.asgi import Depends, api_key_auth_dependency

# 从头部
api_key = api_key_auth_dependency("X-API-Key", position="header")

@app.router.http.get("/data")
async def data(key: Annotated[str, Depends(api_key)]):
    return {"data": "secret"}

# 从查询参数
api_key_query = api_key_auth_dependency("api_key", position="query")

# 从 Cookie
api_key_cookie = api_key_auth_dependency("session", position="cookie")
```

- `position`：`"header"`、`"query"` 或 `"cookie"`
- 返回：API Key 字符串
- 缺失时抛出：`HTTPException(401)`
- OpenAPI：生成带有正确位置的 `ApiKeyAuth` 安全方案

## OpenAPI 集成

所有安全依赖会自动在 `components` 部分生成 OpenAPI `securitySchemes`，并在操作上生成 `security` 要求。

```python
from kui.asgi import Kui, OpenAPI, HttpRoute, Depends, bearer_auth

app = Kui(routes=[
    HttpRoute("/me", me),
])
app.router <<= "/docs" // OpenAPI(
    info={"title": "My API", "version": "1.0.0"},
).routes
```

生成的规格包含：

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

## 自定义认证

创建自己的认证依赖：

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

带有 `Header`/`Query`/`Cookie` 参数的自定义依赖会自动在 OpenAPI 中生成文档，但不会生成 `securitySchemes` 条目。如需自定义安全方案，请使用 `describe_extra_docs`。
