import json
import os
import pprint
import typing

import yaml

from .types import final
from .utils import Singleton

__all__ = ["serve_config"]


class ConfigError(Exception):
    pass


class ConfigFileError(ConfigError):
    pass


class UpperDict(dict):
    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        for key, value in list(self.items()):
            super().__delitem__(key)
            self[key] = value

    def __str__(self) -> str:
        return pprint.pformat(self, indent=4)

    def __setitem__(self, key: str, value: typing.Any) -> None:
        key = key.upper()

        if isinstance(value, dict):
            if key in self.keys():
                for k, v in value.items():
                    self[k.upper()] = v
            else:
                super().__setitem__(key, UpperDict(value))
        else:
            super().__setitem__(key, value)

    def __getitem__(self, key: str) -> typing.Any:
        return super().__getitem__(key.upper())

    def __delitem__(self, key: str) -> None:
        super().__delitem__(key.upper())

    def update(self, m, **kwargs):
        if hasattr(m, "items"):
            m = m.items()

        for key, value in m:
            self[key] = value

        for key, value in kwargs.items():
            self[key] = value


@final
class ServeConfig(UpperDict, metaclass=Singleton):
    ENV: str
    DEBUG: bool
    APP: str
    HOST: str
    PORT: int
    LOG_LEVEL: str
    AUTORELOAD: bool

    def setdefaults(self) -> None:
        """set default values"""

        self["env"] = "dev"
        self["debug"] = True
        self["host"] = "127.0.0.1"
        self["port"] = 4190
        self["log_level"] = "info"
        self["autoreload"] = True

    def __init__(self, *args, **kwargs) -> None:
        super().__setattr__("__editable__", True)
        self.setdefaults()
        self.import_from_file()
        self.import_from_environ()
        super().__setattr__("__editable__", False)

    def import_from_file(self) -> None:
        filename = None

        for _filename in ("index.json", "index.yaml", "index.yml"):
            if os.path.exists(os.path.normpath(_filename)):
                if filename is not None:
                    raise ConfigFileError(
                        f"`{filename}` and `{_filename}` cannot be used at the same project."
                    )
                filename = _filename

        if filename is None:
            return

        with open(filename, "rb") as file:
            if filename.endswith(".json"):
                data = json.load(file)
            elif filename.endswith(".yaml") or filename.endswith(".yml"):
                data = yaml.safe_load(file)

        if not isinstance(data, dict):
            raise ConfigError("config must be a dictionary.")

        self.update(data)

    def import_from_environ(self) -> None:
        result: typing.Dict[str, typing.Any] = {}

        if os.environ.get("INDEX_DEBUG"):
            result["debug"] = os.environ.get("INDEX_DEBUG") in ("on", "True")

        if os.environ.get("INDEX_ENV"):
            result["env"] = os.environ.get("INDEX_ENV")

        self.update(result)

    def __getattr__(self, name: str) -> typing.Any:
        value = self.get(name, ...)
        if value is ...:
            raise AttributeError(
                f"'{self.__class__.__name__}' object has no attribute '{name}'"
            )
        return value

    def __setattr__(self, name: str, value: typing.Any) -> None:
        raise ConfigError("Modifying the attribute value of Config is not allowed.")

    def __delattr__(self, name: str) -> None:
        raise ConfigError("Deleting the attribute value of Config is not allowed.")

    def __setitem__(self, key: str, value: typing.Any) -> None:
        if not self.__editable__:
            raise ConfigError("Modifying the attribute value of Config is not allowed.")
        super().__setitem__(key, value)

    def __delitem__(self, key: str) -> None:
        raise ConfigError("Deleting the attribute value of Config is not allowed.")

    def get(self, key, default=None) -> typing.Any:
        key = key.upper()
        env = super().get(self["env"].upper(), {})
        value = env.get(key, ...)
        if value is ...:
            value = super().get(key, default)
        return value


serve_config = ServeConfig()
