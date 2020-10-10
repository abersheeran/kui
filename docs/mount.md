就像其他 ASGI 框架一样，Index 也提供了挂载其他应用的能力——ASGI 应用或者 WSGI 应用都可以。

## 使用 router 注册

例如：使发往 `/static` 下的 HTTP 请求都交给 [`starlette.staticfiles.StaticFiles`](https://www.starlette.io/staticfiles/#staticfiles) 去处理

```python
from indexpy import Index
from indexpy.routing import ASGIRoute
from starlette.staticfiles import StaticFiles

app = Index()
app.router.append(
    ASGIRoute(
        "/static{filepath:path}",
        StaticFiles(directory="."),
        name="static",
        type=("http",),
    )
)
```

!!! notice
    注册仅支持 WSGI 的 application，应使用 `starlette.middleware.wsgi.WSGIMiddleware` 或 `a2wsgi.WSGIMiddleware` 将其包装转换为支持 ASGI 的 application。
