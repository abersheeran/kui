import asyncio
import typing
import inspect
import functools

from starlette.concurrency import run_in_threadpool


def make_async(
    func: typing.Callable = None, *, only_mark: bool = False
) -> typing.Callable:
    """
    always return a awaitable callable object
    """

    if only_mark and func is None:
        return lambda func: make_async(func, only_mark=True)

    if func is None:
        raise ValueError("`func` must be not None")

    if asyncio.iscoroutinefunction(func):
        return func

    if only_mark:

        @functools.wraps(func)
        async def wrapper(*args, **kwargs) -> typing.Any:
            return await func(*args, **kwargs)  # type: ignore

    else:

        @functools.wraps(func)
        async def wrapper(*args, **kwargs) -> typing.Any:
            return await run_in_threadpool(func, *args, **kwargs)  # type: ignore

    return wrapper


def complicating(func: typing.Callable) -> typing.Callable[..., typing.Awaitable]:
    """
    always return a awaitable callable object
    """
    if asyncio.iscoroutinefunction(func):
        return func

    if not (inspect.isfunction(func) or inspect.ismethod(func)):
        if inspect.isclass(func):
            # class that has `__await__` method
            if hasattr(func, "__await__"):
                return func
        else:
            # callable object
            if asyncio.iscoroutinefunction(getattr(func, "__call__")):
                return func

    @functools.wraps(func)
    async def wrapper(*args, **kwargs) -> typing.Any:
        return await run_in_threadpool(func, *args, **kwargs)

    return wrapper


def keepasync(*args: str) -> typing.Callable[..., object]:
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
        def __new__(
            cls: type,
            clsname: str,
            bases: typing.Tuple[type],
            namespace: typing.Dict[str, typing.Any],
        ):
            for name in args:
                if name not in namespace:
                    continue
                namespace[name] = complicating(namespace[name])
            return type.__new__(cls, clsname, bases, namespace)

    return AlwaysAsyncMeta
