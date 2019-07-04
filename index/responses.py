"""
Maybe more repsonse type will be done in the future
"""
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
from .errors import Http500


def automatic(*args):
    if len(args) > 3:
        raise ValueError("The response cannot exceed three parameters.")

    # Response or Response subclass
    if isinstance(args[0], Response):
        return args[0]

    # judge status code and headers
    try:
        if not isinstance(args[1], int):
            raise TypeError("The response status code must be integer.")

        if not isinstance(args[2], dict):
            raise TypeError("The response headers must be dictionary.")

    except IndexError:
        pass

    if isinstance(args[0], dict):
        return JSONResponse(*args)
    elif isinstance(args[0], str):
        return PlainTextResponse(*args)

    raise TypeError(f"Wrong response type: {type(args[0])}")
