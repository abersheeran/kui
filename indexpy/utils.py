import os
import asyncio
import threading
import importlib
from functools import partial
from types import ModuleType
from typing import (
    TYPE_CHECKING,
    Tuple,
    Dict,
    Any,
    Optional,
    Callable,
)


class Singleton(type):
    def __init__(
        cls, name: str, bases: Tuple[type], namespace: Dict[str, Any],
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
    cached_property = property
else:

    class cached_property:
        """
        A property that is only computed once per instance and then replaces
        itself with an ordinary attribute. Deleting the attribute resets the
        property.
        """

        def __init__(self, func: Callable) -> None:
            self.__doc__ = getattr(func, "__doc__")
            self.func = func

        def __get__(self, obj: Any, cls: Optional[type] = None) -> Any:
            if obj is None:
                return self
            value = obj.__dict__[self.func.__name__] = self.func(obj)
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

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.sync_lock = threading.Lock()
        self.async_lock = asyncio.Lock()

    def __enter__(self):
        self.sync_lock.acquire()
        return self

    def __exit__(self, exc_type, value, traceback):
        self.sync_lock.release()

    async def __aenter__(self):
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
