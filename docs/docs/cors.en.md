# CORS

Cross-Origin Resource Sharing (CORS) controls which origins can access your API from a browser.

## App-Level CORS

Apply CORS to all routes:

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

### Configuration Options

| Option | Type | Default | Description |
|---|---|---|---|
| `allow_origins` | `Iterable[Pattern]` | — | Regex patterns matching allowed origins |
| `allow_methods` | `Iterable[str]` | — | Allowed HTTP methods |
| `allow_headers` | `Iterable[str]` | — | Allowed request headers |
| `expose_headers` | `Iterable[str]` | — | Headers exposed to the browser |
| `allow_credentials` | `bool` | `False` | Allow cookies/auth in cross-origin requests |
| `max_age` | `int` | — | Seconds to cache preflight response |

`allow_origins` uses compiled regex patterns (from the `re` module). To allow all origins:

```python
"allow_origins": [re.compile(".*")]
```

## Per-Route CORS

Apply CORS middleware to specific routes:

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

Or on a Routes group:

```python
from kui.asgi import Routes, HttpRoute

api_routes = Routes(
    HttpRoute("/users", list_users),
    HttpRoute("/posts", list_posts),
    http_middlewares=[allow_cors()],
)
```

## How It Works

The CORS middleware:

1. Checks the `Origin` header against `allow_origins` patterns
2. If the origin matches:
    - For `OPTIONS` preflight requests, returns an empty `200` response with CORS headers
    - For normal requests, calls the endpoint and adds CORS headers to the response
3. If the origin does not match (or no `Origin` header), the request passes through to the endpoint without CORS headers — the browser will block the response client-side

CORS headers added to matching-origin responses:

- `Access-Control-Allow-Origin`
- `Access-Control-Allow-Methods`
- `Access-Control-Allow-Headers`
- `Access-Control-Expose-Headers`
- `Access-Control-Allow-Credentials`
- `Access-Control-Max-Age`
