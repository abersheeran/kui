import importlib


class Singleton(type):

    def __init__(cls, name, bases, namespace):
        cls.instance = None

    def __call__(cls, *args, **kwargs):
        if cls.instance is None:
            cls.instance = super().__call__(*args, **kwargs)
        return cls.instance


def import_module(name: str) -> None:
    """
    try importlib.import_module, nothing to do when ImportError be raised
    """
    try:
        importlib.import_module(name)
    except ImportError:
        pass
