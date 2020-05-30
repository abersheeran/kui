import typing
import traceback
from contextvars import ContextVar
from functools import wraps

from starlette.background import BackgroundTasks as _BackgroundTasks


class BackgroundTasks(_BackgroundTasks):
    async def __call__(self) -> None:
        for task in self.tasks:
            try:
                await task()
            except Exception:
                traceback.print_exc()


after_response_tasks_var: ContextVar[BackgroundTasks] = ContextVar(
    "after_response_tasks"
)
finished_response_tasks_var: ContextVar[BackgroundTasks] = ContextVar(
    "finished_response_tasks"
)


def after_response(func: typing.Callable) -> typing.Callable:
    """call func after response"""

    @wraps(func)
    def wrapper(*args, **kwargs) -> None:
        background_tasks = after_response_tasks_var.get()
        background_tasks.add_task(func, *args, **kwargs)

    return wrapper


def finished_response(func: typing.Callable) -> typing.Callable:
    """call func when response has finished"""

    @wraps(func)
    def wrapper(*args, **kwargs) -> None:
        background_tasks = finished_response_tasks_var.get()
        background_tasks.add_task(func, *args, **kwargs)

    return wrapper
