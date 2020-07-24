Index 是一个基于 ASGI 的异步 web 框架，其应对高并发的秘诀就是使用异步 IO。这意味着你在其中使用任何的同步 IO 操作，都可能会阻塞整个程序的运行。

## make_async

Index 在加载代码时会在各个阶段对处理请求的可调用对象进行检查是否为异步函数，如果检查判断为非异步函数，则会将其固定为在线程池中执行的异步函数。但这种检查对于返回 `asyncio.Future` 的函数或者被重重包裹的函数是困难的。

用户编写代码时，应当使用 `make_async` 装饰器对未使用 `async def` 进行定义的视图函数进行标注，这样 Index 对函数进行检查时将不会做出错误的判断。

如果函数调用了同步 IO：

```python
from indexpy.concurrency import make_async


@make_async
def synchronous_io():
    ...
```

如果函数返回了 `asyncio.Future` 一类的可等待对象：

```python
from indexpy.concurrency import make_async


@make_async(only_mark=True)
def asynchronous_io():
    ...
```

!!! tip
    `@asyncio.coroutine` 会被未来的 Python 版本放弃，所以建议使用 `@make_async(only_mark=True)` 对函数进行异步标注。

!!! notice
    被线程池包裹的异步函数并不是高效的，如果不是无法使用异步 IO 的情况，不要滥用 `@make_async`。
