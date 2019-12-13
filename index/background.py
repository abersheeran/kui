import typing
from contextvars import ContextVar
from functools import wraps

from starlette.background import BackgroundTasks

background_tasks_var: ContextVar[BackgroundTasks] = ContextVar("background_tasks")


def after_response(func: typing.Callable) -> typing.Callable:
    """call func after response"""

    @wraps(func)
    def wrapper(*args, **kwargs) -> None:
        background_tasks = background_tasks_var.get()
        background_tasks.add_task(func, *args, **kwargs)

    return wrapper
