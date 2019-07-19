import os
import threading
import importlib

from watchdog.events import FileSystemEventHandler
from watchdog.observers import Observer

from .config import Config, logger


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
    def __init__(self):
        self.observer = Observer()
        self.observer.schedule(MonitorFileEventHandler(), Config().path, recursive=True)
        self.observer.start()

    def __del__(self):
        """drop observer"""
        # self.observer.stop()
        # self.observer.join()
