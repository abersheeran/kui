"""
Maybe more repsonse type will be done in the future
"""
import functools

from starlette.responses import (
    Response,
    HTMLResponse,
    PlainTextResponse,
    JSONResponse,
    RedirectResponse,
    StreamingResponse,
    FileResponse
)

from .config import logger

__all__ = [
    "register_type",
    "Response",
    "HTMLResponse",
    "PlainTextResponse",
    "JSONResponse",
    "RedirectResponse",
    "StreamingResponse",
    "FileResponse"
]


class AutoResponseType:

    type_map = {}

    @classmethod
    def register_type(cls, type_):
        def register_func(func):
            cls.type_map[type_] = func

            def wrapper(*args, **kwargs):
                return func(*args, **kwargs)
            return wrapper
        return register_func

    @classmethod
    def automatic(cls, *args):

        # Response or Response subclass
        if isinstance(args[0], Response):
            return args[0]

        try:
            return cls.type_map[type(args[0])](*args)
        except KeyError:
            raise TypeError(f"Wrong response type: {type(args[0])}")


register_type = functools.partial(AutoResponseType.register_type)
automatic = functools.partial(AutoResponseType.automatic)


@register_type(dict)
def json_type(*args):
    if len(args) > 3:
        raise ValueError("The response cannot exceed three parameters.")

    # judge status code and headers
    try:
        if not isinstance(args[1], int):
            raise TypeError("The response status code must be integer.")

        if not isinstance(args[2], dict):
            raise TypeError("The response headers must be dictionary.")

    except IndexError:
        pass

    return JSONResponse(*args)


@register_type(str)
def text_type(*args):
    if len(args) > 3:
        raise ValueError("The response cannot exceed three parameters.")

    # judge status code and headers
    try:
        if not isinstance(args[1], int):
            raise TypeError("The response status code must be integer.")

        if not isinstance(args[2], dict):
            raise TypeError("The response headers must be dictionary.")

    except IndexError:
        pass

    return PlainTextResponse(*args)
