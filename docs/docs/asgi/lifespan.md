Kuí 允许注册若干个事件处理程序，以处理在应用程序启动之前或关闭时需要运行的代码。

- on_startup: Kuí 启动之前运行的函数
- on_shutdown: Kuí 关闭之前运行的函数

## 注册事件

你可以用装饰器语法注册事件处理程序，注册普通函数或由 `async def` 定义的异步函数均可。

```python
import logging

from kui.asgi import Kui

app = Kui()
logger = logging.getLogger("example")


@app.on_startup
def logger_on_startup(app: Kui):
    logger.info("Called on startup")


@app.on_shutdown
def logger_on_shutdown(app: Kui):
    logger.info("Called on shutdown")
```

也可以在创建 `Kui` 对象时作为参数传递，以下程序与上等价。

```python
import logging

from kui.asgi import Kui

logger = logging.getLogger("example")


def logger_on_startup(app: Kui):
    logger.info("Called on startup")


def logger_on_shutdown(app: Kui):
    logger.info("Called on shutdown")


app = Kui(
    on_startup=[logger_on_startup],
    on_shutdown=[logger_on_shutdown],
)
```

## `asynccontextmanager`

Kuí 提供了 `asynccontextmanager_lifespan` 函数，它可以将异步生成器函数转换为 `on_startup` 和 `on_shutdown` 事件处理程序。

```python
from kui.asgi.lifespan import asynccontextmanager_lifespan


async def f(app: Kui):
    logger.info("Called on startup")
    yield
    logger.info("Called on shutdown")


on_startup, on_shutdown = asynccontextmanager_lifespan(f)
app = Kui(
    on_startup=[on_startup],
    on_shutdown=[on_shutdown],
)
```
