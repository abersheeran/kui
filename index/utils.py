import os
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


def _import_module(name: str) -> Optional[ModuleType]:
    """
    try importlib.import_module, nothing to do when module not be found.
    """
    from .config import config, logger

    if os.path.exists(os.path.join(config.path, name + ".py")) or os.path.exists(
        os.path.join(config.path, name, "__init__.py")
    ):
        logger.debug(f"Importing {name}")
        return importlib.import_module(name)
    logger.debug(f"Dont found module {name}")
    return None  # nothing to do when module not be found
