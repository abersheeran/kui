import logging

from indexpy import app

logger = logging.getLogger(__name__)


@app.on_startup
def logger_on_startup():
    logger.info("Called on startup")


def logger_on_shutdown():
    logger.info("Called on shutdown")


app.on_shutdown(logger_on_shutdown)
