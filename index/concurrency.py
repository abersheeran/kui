import asyncio
import functools

from starlette.concurrency import run_in_threadpool


def complicating(func):
    """
    always return a coroutine function
    """
    if asyncio.iscoroutinefunction(func):
        return func

    @functools.wraps(func)
    async def wrapper(*args, **kwargs):
        return await run_in_threadpool(func, *args, **kwargs)
    return wrapper
