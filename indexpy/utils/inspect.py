from pathlib import Path
from typing import Any, TypeVar

from typing_extensions import TypeGuard

_ClassType = TypeVar("_ClassType", bound=type)


def safe_issubclass(__cls: Any, __class: _ClassType) -> TypeGuard[_ClassType]:
    return isinstance(__cls, type) and issubclass(__cls, __class)


def get_raw_handler(handler: Any) -> Any:
    """
    Get handler's raw handler.
    """
    while hasattr(handler, "__wrapped__") or hasattr(handler, "__raw_handler__"):
        new_handler = handler

        if hasattr(handler, "__wrapped__"):
            new_handler = handler.__wrapped__
        elif hasattr(handler, "__raw_handler__"):
            new_handler = handler.__raw_handler__

        if new_handler is handler:
            break

        handler = new_handler

    return handler


def get_object_filepath(object: Any) -> str:
    """
    Get object's filepath.
    """
    path = Path(object.__code__.co_filename).absolute()
    try:
        filepath = "./" + path.relative_to(Path.cwd()).as_posix()
    except ValueError:
        filepath = path.as_posix()
    return filepath
