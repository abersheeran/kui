import os
import copy
import functools
import importlib
from types import ModuleType
from typing import Tuple, Dict, Mapping, Any, Iterator, Callable


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


def _import_module(name: str) -> ModuleType:
    """
    try importlib.import_module, nothing to do when module not be found.
    """
    from .config import config

    if os.path.exists(os.path.join(config.path, name + ".py")) or os.path.exists(
        os.path.join(config.path, name, "__init__.py")
    ):
        importlib.import_module(name)


def get_views() -> Iterator[Tuple[ModuleType, str]]:
    from .config import config

    views_path = os.path.join(config.path, "views")

    for root, _, files in os.walk(views_path):
        for file in files:
            if not file.endswith(".py"):
                continue
            if file == "__init__.py":
                continue
            abspath = os.path.join(root, file)
            relpath = os.path.relpath(abspath, config.path).replace("\\", "/")

            module = importlib.import_module(relpath.replace("/", ".")[:-3])

            uri = relpath[len("views"):-3]

            if uri.endswith("/index"):
                uri = uri[:-5]

            yield module, uri


def currying(func: Callable) -> Callable:
    f = func

    @functools.wraps(func)
    def wrapper(*args, **kwargs) -> typing.Any:
        nonlocal f
        if args or kwargs:
            f = functools.partial(f, *args, **kwargs)
            return wrapper
        return f()

    return wrapper


def merge_mapping(x: Mapping, default: Mapping) -> Mapping:
    """merge x to default. return a *new* Mapping"""
    default = copy.deepcopy(default)
    for key, value in x.items():
        if isinstance(default.get(key), typing.Mapping):
            if not isinstance(value, typing.Mapping):
                raise ValueError(
                    f"{key} in default is a mapping, but {key} in x is not mapping."
                )
            merge_mapping(value, default[key])
            continue
        default[key] = x[key]
    return default
