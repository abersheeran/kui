import re
import os
import logging
import threading
import importlib

from watchdog.events import FileSystemEventHandler
from watchdog.observers import Observer

from .config import Config

logger = logging.getLogger(__name__)
config = Config()


class ImportTypeError(Exception):

    def __init__(self, position: str, sentence: str):
        self.position = position
        self.sentence = sentence


class CheckImport:

    def __init__(self):
        self.pattern = re.compile("from (?P<path>.*?) import ")

    def check(self, filepath: str) -> (int, str):
        """
        check `from ... import ...` in file

        https://docs.python.org/zh-cn/3/library/importlib.html#importlib.reload
        """
        with open(filepath, encoding="UTF-8") as file:
            for index, line in enumerate(file.readlines()):
                for path in self.pattern.findall(line):
                    abspath = os.path.join(config.path, path.replace(".", "/")) + ".py"
                    if os.path.isfile(abspath):
                        return index, line.strip()
        return 0, ""

    def __call__(self, path: str) -> bool:
        flag = True
        for root, dirnames, filenames in os.walk(path):
            for filename in filenames:
                if not filename.endswith(".py"):
                    continue
                relpath = os.path.relpath(os.path.join(root, filename), path).replace("\\", "/")
                # check import
                error_line_num, error_sentence = self.check(os.path.join(root, filename))
                if error_line_num > 0:
                    flag = False
                    e = ImportTypeError(f"{relpath} line {error_line_num}", error_sentence)
                    logger.warning(f"Check import type error in {e.position}: '{e.sentence}'")
                    # Preloading
                importlib.import_module(relpath.replace("/", ".")[:-3])
        return flag


class MonitorFileEventHandler(FileSystemEventHandler):

    def dispatch(self, event):
        if not event.src_path.endswith(".py"):
            return
        event.filepath = os.path.relpath(event.src_path, Config().path).replace("\\", "/")[:-3]
        if event.filepath.endswith("/__init__"):
            event.filepath = event.filepath[:-len("/__init__")]
        return super().dispatch(event)

    def on_modified(self, event):
        module_path = ".".join(event.filepath.split("/"))
        logger.debug(f"reloading {event.filepath} as {module_path}")

        def reload():
            module = importlib.import_module(module_path)
            importlib.reload(module)
        threading.Thread(target=reload, daemon=True).start()

    def on_created(self, event):
        module_path = ".".join(event.filepath.split("/"))
        logger.debug(f"loading {event.filepath} as {module_path}")
        threading.Thread(target=importlib.import_module, args=(module_path, ), daemon=True).start()


class MonitorFile:
    def __init__(self, path: str):
        self.observer = Observer()
        self.observer.schedule(MonitorFileEventHandler(), path, recursive=True)
        self.observer.start()

    def __del__(self):
        """drop observer"""
        # self.observer.stop()
        # self.observer.join()
