就像其他 ASGI 框架一样，Index 也提供了挂载其他应用的能力——ASGI 应用或者 WSGI 应用都可以。

## 使用 mount

```python
from indexpy import Index

from otherprogram import app as otherprogram_app
from anotherprogram import app as anotherprogram_app

app = Index()

# mount any wsgi application like flask/django
app.mount("/hello", otherprogram_app, "wsgi")

# mount any asgi application like starlette/responder
app.mount("/hello", anotherprogram_app, "asgi")
```

## 层叠用法

使用 Index 的 mount 功能挂载其他应用，当目标应用抛出一个 404 且未读取 `request.body` 的时候，Index 将会自动寻找下一个匹配对象，直到由 Index 自身进行处理。

这意味 Index 支持下面这样的挂载方式：

```python
from indexpy import Index

from otherprogram import app as otherprogram_app
from anotherprogram import app as anotherprogram_app

app = Index()

# mount any wsgi application like flask/django
app.mount("/hello/django", otherprogram_app, "wsgi")

# mount any asgi application like starlette/responder
app.mount("/hello", anotherprogram_app, "asgi")
```

一个简单的例子：接收到一个路径为 `/hello/django/web` 的请求，如果 `otherprogram_app` 抛出 404，则下一个会由 `anotherprogram_app` 去处理，而不是直接把 `otherprogram_app` 的 404 响应返回给用户 (所有基于 starlette 的框架都是直接返回 404，无论是 FastAPI 还是 responder)。
