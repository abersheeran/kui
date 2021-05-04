from contextvars import ContextVar
from typing import TypeVar

T = TypeVar("T")

def bind_contextvar(contextvar: ContextVar[T]) -> T: ...

del T
