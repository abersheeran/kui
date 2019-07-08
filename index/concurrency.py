import asyncio
import functools

from starlette.concurrency import run_in_threadpool


def complicating(func):
    """
    always return a coroutine function
    """
    if not asyncio.iscoroutinefunction(func):
        func = functools.partial(run_in_threadpool, func)
    return func
