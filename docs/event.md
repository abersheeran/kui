Index-py 允许注册若干个事件处理程序，以处理在应用程序启动之前或关闭时需要运行的代码。

* `on_startup`: Index-py 启动之前运行的函数
* `on_shutdown`: Index-py 关闭之前运行的函数

## 注册事件

你可以用装饰器语法注册事件处理程序，注册普通函数或由 `async def` 定义的异步函数均可。

```python
import logging

from indexpy import Index

app = Index()
logger = logging.getLogger("example")


@app.on_startup
def logger_on_startup():
    logger.info("Called on startup")


@app.on_shutdown
def logger_on_shutdown():
    logger.info("Called on shutdown")
```

也可以在创建 `Index` 对象时作为参数传递，以下程序与上等价。

```python
import logging

from indexpy import Index

logger = logging.getLogger("example")


def logger_on_startup():
    logger.info("Called on startup")


def logger_on_shutdown():
    logger.info("Called on shutdown")


app = Index(
    on_startup=[logger_on_startup],
    on_shutdown=[logger_on_shutdown],
)
```
