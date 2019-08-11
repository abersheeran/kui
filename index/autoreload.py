import re
import os
import logging
import typing
import threading
import importlib

from watchdog.events import FileSystemEventHandler
from watchdog.observers import Observer

from .config import Config

logger = logging.getLogger(__name__)
config = Config()


IMPORT_PATTERN = re.compile("from (?P<path>.*?) import ")


def check(filepath: str) -> typing.Iterable[typing.Tuple[int, str]]:
    """
    check `from ... import ...` in file

    https://docs.python.org/zh-cn/3/library/importlib.html#importlib.reload
    """
    with open(filepath, encoding="UTF-8") as file:
        for index, line in enumerate(file.readlines()):
            for path in IMPORT_PATTERN.findall(line):
                abspath = os.path.join(config.path, path.replace(".", "/")) + ".py"
                if os.path.isfile(abspath):
                    yield index, line.strip()


class ImportTypeError(Exception):

    def __init__(self, position: str, sentence: str):
        self.position = position
        self.sentence = sentence


def _import(abspath: str):
    """
    import module in Config().path

    return: module
    """
    relpath = os.path.relpath(abspath, config.path).replace("\\", "/")[:-3]
    # check import
    for error_line_num, error_sentence in check(abspath):
        flag = False
        e = ImportTypeError(f"{relpath} line {error_line_num}", error_sentence)
        logger.warning(f"Check import type error in {e.position}: '{e.sentence}'")
    # loading
    if relpath.endswith("/__init__"):
        relpath = relpath[:-len("/__init__")]
    return importlib.import_module(relpath.replace("/", "."))


def _reload(abspath: str):
    """
    reload module in Config().path
    """
    module = _import(abspath)
    importlib.reload(module)


def checkall(path: str):
    for root, dirs, files in os.walk(path):
        for file in files:
            if not file.endswith(".py"):
                continue
            abspath = os.path.join(root, file)
            _import(abspath)


class MonitorFileEventHandler(FileSystemEventHandler):

    def dispatch(self, event):
        if not event.src_path.endswith(".py"):
            return
        return super().dispatch(event)

    def on_modified(self, event):
        logger.debug(f"reloading {event.src_path}")
        threading.Thread(target=_reload, args=(event.src_path, ), daemon=True).start()

    def on_created(self, event):
        logger.debug(f"loading {event.src_path}")
        threading.Thread(target=_import, args=(event.src_path, ), daemon=True).start()


class MonitorFile:
    def __init__(self, path: str):
        self.observer = Observer()
        self.observer.schedule(MonitorFileEventHandler(), path, recursive=True)
        self.observer.daemon = True
        self.observer.start()

    def stop(self):
        """drop observer"""
        self.observer.stop()
        self.observer.join()
