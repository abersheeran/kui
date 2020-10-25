import asyncio
import importlib
import inspect
import os
import threading
from functools import partial, update_wrapper
from types import ModuleType
from typing import TYPE_CHECKING, Any, Callable, Dict, Optional, Tuple, TypeVar


class Singleton(type):
    def __init__(
        cls,
        name: str,
        bases: Tuple[type],
        namespace: Dict[str, Any],
    ) -> None:
        cls.instance = None
        super().__init__(name, bases, namespace)

    def __call__(cls, *args, **kwargs) -> Any:
        if cls.instance is None:
            cls.instance = super().__call__(*args, **kwargs)
        return cls.instance


def import_module(name: str) -> Optional[ModuleType]:
    """
    try importlib.import_module, nothing to do when module not be found.
    """
    if os.path.exists(os.path.join(os.getcwd(), name + ".py")) or os.path.exists(
        os.path.join(os.getcwd(), name, "__init__.py")
    ):
        return importlib.import_module(name)
    return None  # nothing to do when module not be found


if TYPE_CHECKING:
    # https://github.com/python/mypy/issues/5107
    # for mypy check and IDE support
    cached_property = property
else:

    class cached_property:
        """
        A property that is only computed once per instance and then replaces
        itself with an ordinary attribute. Deleting the attribute resets the
        property.
        """

        def __init__(self, func: Callable) -> None:
            self.func = func
            update_wrapper(self, func)

        def __get__(self, obj: Any, cls: Any) -> Any:
            if obj is None:
                return self
            result = self.func(obj)
            if inspect.isawaitable(result):
                result = asyncio.ensure_future(result)
            value = obj.__dict__[self.func.__name__] = result
            return value


class superclass:
    """
    Call the method of the specified parent class. The usage is similar
    to `super`, but the difference from `super` is that `superclass`
    only looks for methods in the specified parent class.

    example:
        superclass(Class, obj).function(...)
    """

    def __init__(self, cls: type, instance: Any):
        if cls not in instance.__class__.mro():
            raise ValueError("`cls` must be in parent classes")

        self.__cls = cls
        self.__instance = instance

    def __getattr__(self, name: str) -> Callable[..., Any]:
        if not hasattr(self.__cls, name):
            raise AttributeError(name)

        func = getattr(self.__cls, name)
        return partial(func, self.__instance)


class State(dict):
    """
    An object that can be used to store arbitrary state.
    """

    def __enter__(self):
        if not hasattr(self, "sync_lock"):
            self.sync_lock = threading.Lock()
        self.sync_lock.acquire()
        return self

    def __exit__(self, exc_type, value, traceback):
        self.sync_lock.release()

    async def __aenter__(self):
        if not hasattr(self, "async_lock"):
            self.async_lock = asyncio.Lock()
        await self.async_lock.acquire()
        return self

    async def __aexit__(self, exc_type, value, traceback):
        self.async_lock.release()

    def __setattr__(self, name: Any, value: Any) -> None:
        self[name] = value

    def __getattr__(self, name: Any) -> Any:
        try:
            return self[name]
        except KeyError:
            message = "'{}' object has no attribute '{}'"
            raise AttributeError(message.format(self.__class__.__name__, name))

    def __delattr__(self, name: Any) -> None:
        del self[name]


T = TypeVar("T")


class cached:
    def __init__(self, handler: Callable[..., T]) -> None:
        update_wrapper(self, handler)
        self.handler = handler
        self.__caches: Dict[Any, Any] = {}

    def __call__(self, *args: Any, **kwargs: Any) -> T:
        key = tuple(
            [id(value) for value in args] + [id(value) for value in kwargs.values()]
        )
        if key not in self.__caches:
            self.__caches[key] = self.handler(*args, **kwargs)
        return self.__caches[key]

    def clear(self) -> None:
        self.__caches.clear()
