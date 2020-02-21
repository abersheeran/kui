"""
Load some preset functions into Index
"""
import os
from typing import Optional

from starlette.staticfiles import StaticFiles

from .config import here, Config
from .autoreload import MonitorFile
from .applications import Index

app = Index()

app.mount(
    "/static",
    StaticFiles(directory=os.path.join(here, "static"), check_dir=False),
    "asgi",
)


monitor: Optional[MonitorFile] = None


@app.on_event("startup")
def check_on_startup() -> None:
    # monitor file event
    global monitor
    monitor = MonitorFile(here)


@app.on_event("shutdown")
def clear_check_on_shutdown() -> None:
    global monitor
    if monitor is not None:
        monitor.stop()


@app.on_event("startup")
def create_directories() -> None:
    """
    create directories for static & template
    """
    os.makedirs(os.path.join(here, "views"), exist_ok=True)
    os.makedirs(os.path.join(here, "static"), exist_ok=True)
    os.makedirs(os.path.join(here, "templates"), exist_ok=True)


@app.on_event("shutdown")
def clear_directories() -> None:
    """
    if no files exist in the directory, delete them
    """

    def rmdir(dirpath: str) -> None:
        try:
            os.rmdir(dirpath)
        except OSError:
            pass

    rmdir(os.path.join(here, "views"))
    rmdir(os.path.join(here, "static"))
    rmdir(os.path.join(here, "templates"))
