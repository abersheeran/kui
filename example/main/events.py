from indexpy import app, logger


@app.on_event("startup")
def logger_on_startup():
    logger.info("Called on startup")


@app.on_event("shutdown")
def logger_on_shutdown():
    logger.info("Called on shutdown")
