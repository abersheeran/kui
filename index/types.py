import typing
from inspect import signature
from functools import wraps

from .config import Config


def typeassert(func: typing.Callable) -> typing.Callable:
    """
    Force check parameter type by type hint

    * Parameters that use default values will not be checked
    * Parameters without type hint will not be checked

    """
    # If in optimized mode, disable type checking
    if not Config().DEBUG:
        return func

    @wraps(func)
    def wrapper(*args, **kwargs) -> typing.Any:
        # check params
        sig = signature(func)
        bound_values = sig.bind(*args, **kwargs)
        for name, value in bound_values.arguments.items():
            parameter = sig.parameters[name]

            if parameter.annotation is parameter.empty \
                    or parameter.annotation == typing.Any:
                continue
            if value is parameter.default:
                continue
            if not isinstance(value, parameter.annotation):
                raise TypeError(
                    f'Argument {name} must be {parameter.annotation} but got {type(value)}'
                )
        # check return
        result = func(*args, **kwargs)
        if "return" in func.__annotations__:
            return_type = func.__annotations__['return']
            if result is return_type:
                pass
            elif not isinstance(result, return_type):
                raise TypeError(
                    f'Return must be {return_type} but got {type(result)}'
                )
        return result
    return wrapper


def typeasserts(*ty_args, **ty_kwargs):
    """
    Type checking without parameter annotation

    * Cannot be used to check the return value

    """

    def decorate(func):
        # If in optimized mode, disable type checking
        if not Config().DEBUG:
            return func

        # Map function argument names to supplied types
        sig = signature(func)
        bound_types = sig.bind_partial(*ty_args, **ty_kwargs).arguments

        @wraps(func)
        def wrapper(*args, **kwargs):
            bound_values = sig.bind(*args, **kwargs)
            # Enforce type assertions across supplied arguments
            for name, value in bound_values.arguments.items():
                if name in bound_types:
                    if not isinstance(value, bound_types[name]):
                        raise TypeError(
                            f'Argument {name} must be {bound_types[name]} but got {type(value)}'
                        )
            return func(*args, **kwargs)
        return wrapper
    return decorate
