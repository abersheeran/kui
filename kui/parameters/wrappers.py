from __future__ import annotations

import functools
from typing import Callable, TypeVar

CallableObject = TypeVar("CallableObject", bound=Callable)


def _create_new_class(cls):
    """
    Create a fake class for auto-bound parameters.
    """

    @functools.wraps(cls, updated=())
    class NewClass(cls):
        pass

    return NewClass


def create_auto_params(
    create_new_callback: Callable[[CallableObject], CallableObject],
) -> Callable[[CallableObject], CallableObject]:
    """
    Create auto_params
    """

    def auto_params(handler: CallableObject) -> CallableObject:
        if hasattr(handler, "__methods__"):
            new_class = _create_new_class(handler)
            for method in map(lambda x: x.lower(), handler.__methods__):
                old_callback = getattr(handler, method)
                new_callback = create_new_callback(old_callback)
                setattr(new_class, method, new_callback)  # note: set to new class
            setattr(
                new_class,
                "__raw_handler__",
                getattr(handler, "__raw_handler__", handler),
            )
            return new_class  # type: ignore
        else:
            old_callback = handler
            new_callback = create_new_callback(old_callback)
            setattr(
                new_callback,
                "__raw_handler__",
                getattr(handler, "__raw_handler__", handler),
            )
            return new_callback

    return auto_params


def update_wrapper(
    new_handler: CallableObject, old_handler: Callable
) -> CallableObject:
    """
    Update wrapper for auto-bound parameters.
    """
    for attr in dir(old_handler):
        if attr.startswith("__docs_") or attr in ("__method__", "__methods__"):
            setattr(new_handler, attr, getattr(old_handler, attr))

    setattr(new_handler, "__raw_handler__", old_handler)

    return new_handler
