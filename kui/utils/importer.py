from __future__ import annotations

import importlib
import os
from functools import reduce
from types import ModuleType
from typing import Any, Optional


def import_from_string(import_str: str) -> Any:
    module_str, _, attrs_str = import_str.partition(":")
    if not module_str or not attrs_str:
        raise ValueError(
            f'Import string "{import_str}" must be in format "<module>:<attribute>".'
        )

    return reduce(getattr, attrs_str.split("."), importlib.import_module(module_str))


def import_module(name: str) -> Optional[ModuleType]:
    """
    try importlib.import_module, nothing to do when module not be found.
    """
    if os.path.exists(os.path.join(os.getcwd(), name + ".py")) or os.path.exists(
        os.path.join(os.getcwd(), name, "__init__.py")
    ):
        return importlib.import_module(name)
    return None  # nothing to do when module not be found
