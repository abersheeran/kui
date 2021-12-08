from __future__ import annotations

import functools
from inspect import isfunction
from typing import TYPE_CHECKING, Any, Callable, List, TypeVar
from typing import cast as typing_cast

from .requests import request
from .responses import HttpResponse

FuncView = TypeVar("FuncView", bound=Callable)


def required_method(method: str) -> Callable[[FuncView], FuncView]:
    """
    Set the acceptable request method of the function
    """
    allow_methods = {"HEAD", "GET"} if method == "GET" else {method}
    headers = {"Allow": ", ".join(allow_methods)}

    def decorator(function: FuncView) -> FuncView:
        if not isfunction(function):
            raise TypeError("`required_method` can only decorate function")

        @functools.wraps(function)
        def wrapper(*args, **kwargs):
            if request.method in allow_methods:
                return function(*args, **kwargs)
            elif request.method == "OPTIONS":
                return HttpResponse(headers=headers)
            else:
                return HttpResponse(status_code=405, headers=headers)

        setattr(wrapper, "__method__", method.upper())
        return typing_cast(FuncView, wrapper)

    return decorator


class HttpViewMeta(type):
    def __call__(self, *args: Any, **kwds: Any) -> Any:
        instance = super().__call__(*args, **kwds)
        return instance.__impl__()


class HttpView(metaclass=HttpViewMeta):
    HTTP_METHOD_NAMES = [
        "get",
        "post",
        "put",
        "patch",
        "delete",
        "head",
        "options",
        "trace",
    ]

    if TYPE_CHECKING:
        __methods__: List[str]

    def __init_subclass__(cls) -> None:
        cls.__methods__ = [m.upper() for m in cls.HTTP_METHOD_NAMES if hasattr(cls, m)]

    def __impl__(self) -> Any:
        handler = getattr(self, request.method.lower(), self.http_method_not_allowed)
        return handler()

    def http_method_not_allowed(self) -> HttpResponse:
        return HttpResponse(
            status_code=405, headers={"Allow": ", ".join(self.__methods__)}
        )

    def options(self) -> HttpResponse:
        """Handle responding to requests for the OPTIONS HTTP verb."""
        return HttpResponse(headers={"Allow": ", ".join(self.__methods__)})
