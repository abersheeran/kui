import asyncio
import typing
import inspect
import functools

from starlette.concurrency import run_in_threadpool


def complicating(func: typing.Callable) -> typing.Callable:
    """
    always return a coroutine function
    """
    if not(inspect.isfunction(func) or inspect.ismethod(func)):
        if inspect.iscoroutinefunction(func.__call__):
            return func.__call__

    if asyncio.iscoroutinefunction(func):
        return func

    @functools.wraps(func)
    async def wrapper(*args, **kwargs):
        return await run_in_threadpool(func, *args, **kwargs)
    return wrapper


def keepasync(*args):
    """
    Ensure that the specified method must be an asynchronous function

    example:

        class T(metaclass=keepasync("a", "b")):
            def a(self):
                pass

            async def b(self):
                pass
    """
    class AlwaysAsyncMeta(type):
        def __new__(cls, clsname, bases, clsdict):
            for name in args:
                if name not in clsdict:
                    continue
                clsdict[name] = complicating(clsdict[name])
            return super().__new__(cls, clsname, bases, clsdict)
    return AlwaysAsyncMeta
