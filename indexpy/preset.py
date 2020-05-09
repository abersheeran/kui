"""
Load some preset functions into Index
"""
import os
import logging
from typing import Optional

from .config import here
from .autoreload import MonitorFile

logging.getLogger("multipart").setLevel(logging.INFO)


monitor: Optional[MonitorFile] = None


def check_on_startup() -> None:
    # monitor file event
    global monitor
    monitor = MonitorFile(here)


def clear_check_on_shutdown() -> None:
    global monitor
    if monitor is not None:
        monitor.stop()


def create_directories() -> None:
    """
    create directories for static & template
    """
    os.makedirs(os.path.join(here, "views"), exist_ok=True)
    os.makedirs(os.path.join(here, "static"), exist_ok=True)


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
