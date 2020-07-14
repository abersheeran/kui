import asyncio
from functools import wraps, partial

import pytest

from indexpy.concurrency import complicating, keepasync


@pytest.mark.asyncio
async def test_complicating_0():
    class AsyncCall:
        async def __call__(self):
            pass

    await AsyncCall()()
    asyncfunc = AsyncCall()
    assert complicating(asyncfunc) is asyncfunc


@pytest.mark.asyncio
async def test_complicating_1():
    class AsyncClass:
        def __await__(self):
            return self.dispatch().__await__()

        async def dispatch(self):
            pass

    await AsyncClass()
    assert complicating(AsyncClass).__name__ == "AsyncClass"

    await AsyncClass().dispatch()
    assert complicating(AsyncClass.dispatch) is AsyncClass.dispatch


@pytest.mark.asyncio
async def test_complicating_2():
    async def async_func():
        pass

    await async_func()
    assert complicating(async_func) is async_func


@pytest.mark.asyncio
async def test_complicating_3():
    def d(func):
        @wraps(func)
        def f(*args, **kwargs):
            return func(*args, **kwargs)

        return f

    @d
    async def t():
        pass

    assert complicating(t) is t


@pytest.mark.asyncio
async def test_complicating_4():
    @asyncio.coroutine
    def t():
        pass

    await t()
    assert complicating(t) is t


@pytest.mark.asyncio
async def test_complicating_5():
    def func():
        """t"""

    await complicating(func)()
    assert asyncio.iscoroutinefunction(complicating(func))
    assert complicating(func).__name__ == func.__name__
    assert complicating(func).__doc__ == func.__doc__


@pytest.mark.asyncio
async def test_complicating_6():
    async def func(a):
        """t"""
        return a

    func = partial(func, a=1)

    assert 1 == await complicating(func)()


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


@pytest.mark.asyncio
async def test_keepasync_subclass():
    class Base(metaclass=keepasync("hello", "test")):
        def hello(self):
            pass

    class Sub(Base):
        def test(self):
            pass

    await Sub().hello()
    await Sub().test()
    assert Sub.test.__name__ == "test"
