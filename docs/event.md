Index 允许注册若干个事件处理程序，以处理在应用程序启动之前或关闭时需要运行的代码。

* `startup`: 启动之前运行的函数
* `shutdown`: 关闭之前运行的函数

## 注册事件

在项目根目录下建立 `events.py` 写入注册事件的代码。

你可以用装饰器语法注册事件处理程序

```python
from index import app
from index.config import logger


@app.on_event("startup")
def logger_on_startup():
    logger.info("Called on startup")


@app.on_event("shutdown")
def logger_on_shutdown():
    logger.info("Called on shutdown")
```

或者像一个常规函数一样调用

```python
from index import app


async def open_database_connection_pool():
    ...

async def close_database_connection_pool():
    ...

app.add_event_handler('startup', open_database_connection_pool)
app.add_event_handler('shutdown', close_database_connection_pool)
```

!!! tip
    `startup` 与 `shutdown` 两种类型的函数均可以注册任意个，不需要把所有功能写进一个函数里（尽量保证函数功能单一）。
