from __future__ import annotations

import inspect
import sys
from collections import deque
from typing import Any, Callable, Generic, Iterable, TypeVar

if sys.version_info >= (3, 10):  # pragma: no cover
    from typing import ParamSpec
else:  # pragma: no cover
    from typing_extensions import ParamSpec

P = ParamSpec("P")
R = TypeVar("R")


class BackgroundTask(Generic[P, R]):
    """
    Background task.
    """

    def __init__(self, func: Callable[P, R], *args: P.args, **kwargs: P.kwargs) -> None:
        self.func = func
        self.args = args
        self.kwargs = kwargs

    def __call__(self) -> R:
        return self.func(*self.args, **self.kwargs)


class BackgroundTasks(BackgroundTask):
    def __init__(self, tasks: Iterable[BackgroundTask] | None = None):
        self.tasks: deque[BackgroundTask] = deque(tasks) if tasks else deque()

    def append(self, func: Callable[P, Any], *args: P.args, **kwargs: P.kwargs) -> None:
        task = BackgroundTask(func, *args, **kwargs)
        self.tasks.append(task)

    async def run(self) -> None:
        for task in self.tasks:
            result = task()
            if inspect.isawaitable(result):
                await result
