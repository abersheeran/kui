from __future__ import annotations

import asyncio
import importlib
import os
import threading
from contextvars import ContextVar
from functools import partial
from inspect import isclass
from types import ModuleType
from typing import TYPE_CHECKING, Any, Dict, Generic, Optional, Tuple, TypeVar, Union


def safe_issubclass(
    __cls: Any, __class_or_tuple: Union[type, Tuple[Union[type, Tuple[Any, ...]], ...]]
) -> bool:
    return isclass(__cls) and issubclass(__cls, __class_or_tuple)


T = TypeVar("T")


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


class F(partial):
    """
    Python Pipe. e.g.`range(10) | F(filter, lambda x: x % 2) | F(sum)`

    WRANING: There will be a small performance loss when building a
    pipeline. Please do not use it in performance-sensitive locations.
    """

    def __ror__(self, other: Any) -> Any:
        """
        Implement pipeline operators `var | F(...)`
        """
        return self(other)


if TYPE_CHECKING:

    def bind_contextvar(contextvar: ContextVar[T]) -> T:
        raise NotImplementedError


else:

    def bind_contextvar(contextvar):
        class ContextVarBind:
            __slots__ = ()

            def __getattr__(self, name):
                return getattr(contextvar.get(), name)

            def __setattr__(self, name, value):
                setattr(contextvar.get(), name, value)

            def __delattr__(self, name):
                delattr(contextvar.get(), name)

            def __getitem__(self, index):
                return contextvar.get()[index]

            def __setitem__(self, index, value):
                contextvar.get()[index] = value

            def __delitem__(self, index):
                del contextvar.get()[index]

        return ContextVarBind()


class ImmutableAttribute(Generic[T]):
    def __set_name__(self, owner: object, name: str) -> None:
        self.public_name = name
        self.private_name = "_" + name

    def __get__(self, instance: object, cls: type = None) -> T:
        return getattr(instance, self.private_name)

    def __set__(self, instance: object, value: T) -> None:
        if hasattr(instance, self.private_name):
            raise RuntimeError(
                f"{instance.__class__.__name__}.{self.public_name} is immutable"
            )
        setattr(instance, self.private_name, value)

    def __delete__(self, instance: object) -> None:
        raise RuntimeError(
            f"{instance.__class__.__name__}.{self.public_name} is immutable"
        )
