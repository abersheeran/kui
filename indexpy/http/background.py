import sys
import typing
import traceback
from logging import getLogger
from contextvars import ContextVar
from functools import wraps

from starlette.background import BackgroundTasks as _BackgroundTasks


logger = getLogger(__name__)


class BackgroundTasks(_BackgroundTasks):
    async def __call__(self) -> None:
        for task in self.tasks:
            try:
                await task()
            except Exception:
                logger.error(
                    "Background task failed to run:\n"
                    + "".join(traceback.format_exception(*sys.exc_info()))
                )


after_response_tasks_var: ContextVar[BackgroundTasks] = ContextVar(
    "after_response_tasks"
)


def after_response(func: typing.Callable) -> typing.Callable:
    """call func after response"""

    @wraps(func)
    def wrapper(*args, **kwargs) -> None:
        background_tasks = after_response_tasks_var.get()
        background_tasks.add_task(func, *args, **kwargs)

    return wrapper
