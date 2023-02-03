from __future__ import annotations

import typing as t
from contextvars import ContextVar

__all__ = ["bind_contextvar"]

T = t.TypeVar("T")


def bind_contextvar(contextvar: ContextVar[T]) -> T:
    class ContextVarBind:
        __slots__ = ()

        def __getattr__(self, name):
            return getattr(contextvar.get(), name)

        def __setattr__(self, name, value):
            setattr(contextvar.get(), name, value)

        def __delattr__(self, name):
            delattr(contextvar.get(), name)

        def __getitem__(self, index):
            return contextvar.get()[index]  # type: ignore

        def __setitem__(self, index, value):
            contextvar.get()[index] = value  # type: ignore

        def __delitem__(self, index):
            del contextvar.get()[index]  # type: ignore

    return ContextVarBind()  # type: ignore
