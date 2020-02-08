就像其他 ASGI 框架一样，Index 也提供了挂载其他应用的能力——ASGI 应用或者 WSGI 应用都可以。

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
