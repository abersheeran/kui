# CORS

跨源资源共享（CORS）控制哪些源可以从浏览器访问你的 API。

## 应用级 CORS

为所有路由应用 CORS：

```python
import re
from kui.asgi import Kui

app = Kui(
    cors_config={
        "allow_origins": [re.compile(r"https://example\.com")],
        "allow_methods": ["GET", "POST", "PUT", "DELETE"],
        "allow_headers": ["Authorization", "Content-Type"],
        "expose_headers": ["X-Request-Id"],
        "allow_credentials": False,
        "max_age": 600,
    }
)
```

### 配置选项

| 选项 | 类型 | 默认值 | 说明 |
|---|---|---|---|
| `allow_origins` | `Iterable[Pattern]` | — | 匹配允许源的正则表达式 |
| `allow_methods` | `Iterable[str]` | — | 允许的 HTTP 方法 |
| `allow_headers` | `Iterable[str]` | — | 允许的请求头 |
| `expose_headers` | `Iterable[str]` | — | 暴露给浏览器的头部 |
| `allow_credentials` | `bool` | `False` | 允许跨域请求携带 Cookie/认证 |
| `max_age` | `int` | — | 预检响应缓存秒数 |

`allow_origins` 使用编译后的正则表达式（来自 `re` 模块）。允许所有源：

```python
"allow_origins": [re.compile(".*")]
```

## 单路由 CORS

为特定路由应用 CORS 中间件：

```python
import re
from kui.asgi import HttpRoute, allow_cors

cors = allow_cors(
    allow_origins=[re.compile(r"https://.*\.example\.com")],
    allow_methods=["GET", "POST"],
    allow_headers=["Authorization"],
    max_age=3600,
)

app.router <<= HttpRoute("/api/data", handler) @ cors
```

或在 Routes 分组上：

```python
from kui.asgi import Routes, HttpRoute

api_routes = Routes(
    HttpRoute("/users", list_users),
    HttpRoute("/posts", list_posts),
    http_middlewares=[allow_cors()],
)
```

## 工作原理

CORS 中间件：

1. 检查 `Origin` 头部是否匹配 `allow_origins` 模式
2. 如果源匹配：
    - 对 `OPTIONS` 预检请求，返回空的 `200` 响应并附带 CORS 头
    - 对普通请求，调用端点并在响应中添加 CORS 头
3. 如果源不匹配（或没有 `Origin` 头部），请求直接传递到端点，不添加 CORS 头——浏览器会在客户端阻止响应

匹配源响应中添加的 CORS 头部：

- `Access-Control-Allow-Origin`
- `Access-Control-Allow-Methods`
- `Access-Control-Allow-Headers`
- `Access-Control-Expose-Headers`
- `Access-Control-Allow-Credentials`
- `Access-Control-Max-Age`
