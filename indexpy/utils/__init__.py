from __future__ import annotations

import importlib
import os
from inspect import isclass
from types import ModuleType
from typing import Any, Dict, Generic, Optional, Tuple, TypeVar, Union

from .contextvars import bind_contextvar
from .pipe import FF, F
from .state import State

__all__ = [
    "bind_contextvar",
    "FF",
    "F",
    "State",
    "safe_issubclass",
    "Singleton",
    "import_module",
    "ImmutableAttribute",
]


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
