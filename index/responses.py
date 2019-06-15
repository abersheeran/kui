"""
Maybe some packaging will be done in the future
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


def auto(*args):
    if len(args) > 3:
        logger.error("The response cannot exceed three parameters.")
        raise Http500()

    try:
        if not isinstance(args[1], int):
            logger.error("The response status code must be integer.")
            raise Http500()

        if not isinstance(args[2], dict):
            logger.error("The response headers must be dictionary.")
            raise Http500()

    except IndexError:
        pass

    if isinstance(args[0], dict):
        return JSONResponse(*args)
    elif isinstance(args[0], str):
        return PlainTextResponse(*args)
