import asyncio

import pytest

from index.concurrency import complicating, keepasync


@pytest.mark.asyncio
async def test_complicating():
    class AsyncCall:
        async def __call__(self):
            pass
    await AsyncCall()()
    assert complicating(AsyncCall) is AsyncCall.__call__

    class AsyncClass:
        def __await__(self):
            return self.dispatch().__await__()

        async def dispatch(self):
            pass
    await AsyncClass()
    assert complicating(AsyncClass).__name__ == "AsyncClass"

    await AsyncClass().dispatch()
    assert complicating(AsyncClass.dispatch) is AsyncClass.dispatch

    async def async_func():
        pass
    await async_func()
    assert complicating(async_func) is async_func

    def func():
        """t"""
    await complicating(func)()
    assert asyncio.iscoroutinefunction(complicating(func))
    assert complicating(func).__name__ == func.__name__
    assert complicating(func).__doc__ == func.__doc__


@pytest.mark.asyncio
async def test_keepasync():

    class Test(metaclass=keepasync("hello", "test")):

        def hello(self):
            pass

        async def test(self):
            pass

    await Test().hello()
    await Test().test()
    assert Test.test.__name__ == "test"
