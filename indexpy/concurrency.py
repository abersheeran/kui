from __future__ import annotations

import asyncio
import contextvars
import functools
import typing
from typing import (
    Any,
    AsyncGenerator,
    Awaitable,
    Callable,
    Generator,
    Iterator,
    TypeVar,
    overload,
)

from .utils import is_async_gen_callable, is_coroutine_callable, is_gen_callable

T = TypeVar("T")


async def run_in_threadpool(func: Callable[..., T], *args: Any, **kwargs: Any) -> T:
    """
    Run function in threadpool.
    """
    loop = asyncio.get_running_loop()
    child = functools.partial(func, *args, **kwargs)
    context = contextvars.copy_context()
    return typing.cast(T, await loop.run_in_executor(None, context.run, child))


class _StopIteration(Exception):
    pass


def _next(iterator: Iterator[T]) -> T:
    try:
        return next(iterator)
    except StopIteration:
        raise _StopIteration


async def iterate_in_threadpool(iterator: Iterator[T]) -> AsyncGenerator[T, None]:
    """
    Convert iterator to async generator.
    """
    loop = asyncio.get_running_loop()
    context = contextvars.copy_context()
    while True:
        try:
            child = functools.partial(_next, iterator)
            yield typing.cast(T, await loop.run_in_executor(None, context.run, child))
        except _StopIteration:
            break


@overload
def always_async(  # type: ignore
    func: Callable[..., Generator[T, None, None]]
) -> Callable[..., AsyncGenerator[T, None]]:
    ...


@overload
def always_async(func: Callable[..., T]) -> Callable[..., Awaitable[T]]:
    ...


def always_async(func):
    if is_coroutine_callable(func) or is_async_gen_callable(func):
        return func

    if is_gen_callable(func):

        @functools.wraps(func)
        async def wrapper_gen(*args, **kwargs):
            generator = func(*args, **kwargs)
            async for item in iterate_in_threadpool(generator):
                yield item

        return wrapper_gen

    else:

        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            return await run_in_threadpool(func, *args, **kwargs)

        return wrapper
