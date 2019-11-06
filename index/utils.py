import os
import typing
import importlib


class Singleton(type):
    def __init__(
        cls,
        name: str,
        bases: typing.Iterable[str],
        namespace: typing.Dict[str, typing.Any],
    ) -> None:
        cls.instance = None

    def __call__(cls, *args, **kwargs) -> typing.Any:
        if cls.instance is None:
            cls.instance = super().__call__(*args, **kwargs)
        return cls.instance


def _import_module(name: str) -> None:
    """
    try importlib.import_module, nothing to do when ImportError be raised
    """
    from .config import config

    try:
        importlib.import_module(name)
    except ImportError:
        pass
