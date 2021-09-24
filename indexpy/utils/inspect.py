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

        if hasattr(handler, "__raw_handler__"):
            new_handler = handler.__raw_handler__

        if new_handler is handler:
            break

        handler = new_handler

    return handler
