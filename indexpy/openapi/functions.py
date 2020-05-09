import typing


def describe(
    status: int, response_model: typing.Any = None, description: str = ""
) -> typing.Callable:
    """bind status => response model in http handler"""

    def decorator(func: typing.Callable) -> typing.Callable:
        """bind response model"""
        if hasattr(func, "__resps__"):
            getattr(func, "__resps__")[status] = {"model": response_model}
        else:
            setattr(func, "__resps__", {status: {"model": response_model}})

        getattr(func, "__resps__")[status]["description"] = description

        return func

    return decorator
