from __future__ import annotations

import asyncio
import contextvars
import functools
from typing import Any, AsyncGenerator, Awaitable, Callable, Iterator, TypeVar, Union

from indexpy.utils.inspect import is_async_gen_callable

from .utils import is_coroutine_callable, is_gen_callable

T = TypeVar("T")


async def run_in_threadpool(func: Callable[..., T], *args: Any, **kwargs: Any) -> T:
    loop = asyncio.get_running_loop()
    child = functools.partial(func, *args, **kwargs)
    context = contextvars.copy_context()
    return await loop.run_in_executor(None, context.run, child)


class _StopIteration(Exception):
    pass


def _next(iterator: Iterator[T]) -> T:
    try:
        return next(iterator)
    except StopIteration:
        raise _StopIteration


async def iterate_in_threadpool(iterator: Iterator[T]) -> AsyncGenerator[T, None]:
    while True:
        try:
            yield await run_in_threadpool(_next, iterator)
        except _StopIteration:
            break


def always_async(
    func: Callable[..., T],
) -> Union[Callable[..., AsyncGenerator[T, None]], Callable[..., Awaitable[T]]]:
    if is_coroutine_callable(func) or is_async_gen_callable(func):
        return func

    if is_gen_callable(func):

        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            generator = func(*args, **kwargs)
            async for item in iterate_in_threadpool(generator):
                yield item

    else:

        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            return await run_in_threadpool(func, *args, **kwargs)

    return wrapper
