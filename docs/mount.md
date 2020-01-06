就像其他 ASGI 框架一样，Index 也提供了挂载其他应用的能力——ASGI 应用或者 WSGI 应用都可以。

不同的是，Index 提供了更加友好的挂载方法。当挂载的其他 app 抛出了一个 404(not found) 状态时，Index 会继续寻找下一个匹配的可能，直到遇到一个非 404 的响应。

如果所有挂载的 app 都抛出 404 响应，那么最终将由 Index 自身进行处理此次请求。

## 使用 mount

在项目根目录下建立 `mounts.py` 文件，在其中挂载其他 app。

```python
from index import app

from otherprogram import app as otherprogram_app
from anotherprogram import app as anotherprogram_app

# mount any wsgi application like flask/django
app.mount("/hello", otherprogram_app, "wsgi")

# mount any asgi application like starlette/responder
app.mount("/hello", anotherprogram_app, "asgi")
```
