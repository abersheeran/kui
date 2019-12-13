import copy
import typing
import functools


def currying(func: typing.Callable) -> typing.Callable:
    f = func

    @functools.wraps(func)
    def wrapper(*args, **kwargs) -> typing.Any:
        nonlocal f
        if args or kwargs:
            f = functools.partial(f, *args, **kwargs)
            return wrapper
        return f()

    return wrapper


def merge_mapping(x: typing.Mapping, default: typing.Mapping) -> typing.Mapping:
    """merge x to default. return a *new* Mapping"""
    default = copy.deepcopy(default)
    for key, value in x.items():
        if isinstance(default.get(key), typing.Mapping):
            if not isinstance(value, typing.Mapping):
                raise ValueError(
                    f"{key} in default is a mapping, but {key} in x is not mapping."
                )
            merge_mapping(value, default[key])
            continue
        default[key] = x[key]
    return default
