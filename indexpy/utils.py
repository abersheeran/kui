import os
import threading
import importlib
from types import ModuleType
from typing import Tuple, Dict, Any, Optional


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


class State(dict):
    """
    An object that can be used to store arbitrary state.
    """

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self._lock = threading.Lock()

    def __enter__(self):
        self._lock.acquire()
        return self

    def __exit__(self, exc_type, value, traceback):
        self._lock.release()

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
