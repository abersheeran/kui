就像其他 ASGI 框架一样，Index 也提供了挂载其他应用的能力——ASGI 应用或者 WSGI 应用都可以。

## 使用 mount

```python
from indexpy import Index

from otherprogram import app as otherprogram_app
from anotherprogram import app as anotherprogram_app

app = Index()

# mount any wsgi application like flask/django
app.mount_wsgi("/hello", otherprogram_app)

# mount any asgi application like starlette/responder
app.mount_asgi("/hello", anotherprogram_app)
```

### 层叠用法

使用 Index 的 mount 功能挂载其他应用，当目标应用抛出一个 404 且未读取 `request.body` 的时候，Index 将会自动寻找下一个匹配对象，直到由 Index 自身进行处理。

在上面的代码中：接收到一个路径为 `/hello/django/web` 的请求，如果 `otherprogram_app` 抛出 404，则下一个会由 `anotherprogram_app` 去处理，而不是直接把 `otherprogram_app` 的 404 响应返回给用户。

## 使用 router 注册

如上的 `mount` 往往在无法确认最终由哪一个 app 进行处理请求时使用，但在更多的时候，你应当能确定这些信息，而这个时候推荐使用 `app.router` 对路由进行注册。例如：使发往 `/static` 下的 HTTP 请求都交给 [`starlette.staticfiles.StaticFiles`](https://www.starlette.io/staticfiles/#staticfiles) 去处理

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
