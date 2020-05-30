import re
import os
import time
import logging
import typing
import threading
import importlib
from types import ModuleType

from watchdog.events import FileSystemEventHandler, FileSystemEvent
from watchdog.observers import Observer

from .config import Config

logging.getLogger("watchdog").setLevel(logging.INFO)
logger = logging.getLogger(__name__)


IMPORT_PATTERN = re.compile("from (?P<name>.*?) import ")


class ReloadImport:
    def __init__(self) -> None:
        self.import_mapping: typing.Dict[str, typing.Set[str]] = {}
        here = os.getcwd()
        for name in os.listdir(here):
            abspath = os.path.join(here, name)
            if os.path.isdir(abspath):
                self._parse_dir(abspath)
            elif os.path.isfile(abspath):
                self._parse_file(abspath)

    def _parse_dir(self, dirpath: str) -> None:
        all_name = os.listdir(dirpath)
        if "__init__.py" not in all_name:
            return
        for name in all_name:
            abspath = os.path.join(dirpath, name)
            if os.path.isdir(abspath):
                self._parse_dir(abspath)
            if not os.path.isfile(abspath):
                continue
            self._parse_file(abspath)

    def _parse_file(self, abspath: str) -> None:
        if not abspath.endswith(".py"):
            return None

        _module_ = self.module_name(abspath)
        with open(abspath, encoding="UTF-8") as file:
            for module_name in IMPORT_PATTERN.findall(file.read()):
                if module_name in self.import_mapping:
                    self.import_mapping[module_name].add(_module_)
                else:
                    self.import_mapping[module_name] = {
                        _module_,
                    }

    @staticmethod
    def module_name(abspath: str) -> str:
        """
        Get module name from a abspath.
        """
        assert abspath.endswith(".py"), abspath
        relpath = os.path.relpath(abspath, os.getcwd()).replace("\\", "/")[:-3]
        if relpath.endswith("/__init__"):
            relpath = relpath[: -len("/__init__")]
        return relpath.replace("/", ".")

    def _import(
        self, abspath: str, *, sleep: bool = True
    ) -> typing.Optional[ModuleType]:
        """
        import module

        return: module
        """
        if sleep:  # when VSCode formats code, a temporary file will be created.
            time.sleep(1.3)
            if not os.path.exists(abspath):
                return None

        self._parse_file(abspath)

        try:
            return importlib.import_module(self.module_name(abspath))
        except SyntaxError:
            logger.debug(f"load fail {abspath}")
        return None

    def _reload(self, abspath: str) -> typing.Optional[ModuleType]:
        """
        reload module

        return: module
        """

        _module_ = self._import(abspath, sleep=False)
        if _module_:
            importlib.reload(_module_)

        for _module_name in self.import_mapping.get(self.module_name(abspath), set()):
            _abspath = os.path.join(os.getcwd(), *_module_name.split("."))
            if os.path.isdir(_abspath):
                _abspath = os.path.join(_abspath, "__init__")
            _abspath += ".py"
            self._reload(_abspath)

        return _module_


class MonitorFileEventHandler(FileSystemEventHandler):
    def __init__(self) -> None:
        self.reload_import = ReloadImport()

    def dispatch(self, event: FileSystemEvent):
        config = Config()
        if not config.HOTRELOAD or config.AUTORELOAD:
            return
        if not event.src_path.endswith(".py"):
            return
        return super().dispatch(event)

    def on_modified(self, event: FileSystemEvent):
        logger.debug(f"reloading {event.src_path}")
        threading.Thread(
            target=self.reload_import._reload, args=(event.src_path,), daemon=True
        ).start()

    def on_created(self, event: FileSystemEvent):
        logger.debug(f"loading {event.src_path}")
        threading.Thread(
            target=self.reload_import._import, args=(event.src_path,), daemon=True
        ).start()


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
