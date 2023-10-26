Kuí allows registering multiple event handlers to run code before the application starts or before it shuts down.

- on_startup: Function to run before Kuí starts
- on_shutdown: Function to run before Kuí shuts down

## Registering Events

You can register event handlers using decorator syntax. Both regular functions and async functions defined with `async def` can be registered.

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

You can also pass them as arguments when creating the `Kui` object. The following code is equivalent to the previous example.

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

Kuí provides the `asynccontextmanager_lifespan` function, which can convert an async generator function into `on_startup` and `on_shutdown` event handlers.

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
