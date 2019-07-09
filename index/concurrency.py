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
        result = await run_in_threadpool(func, *args, **kwargs)
        if asyncio.iscoroutine(result):
            return await result
        return result
    return wrapper
