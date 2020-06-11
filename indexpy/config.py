import os
import json
import typing
import logging

import yaml

from .utils import Singleton

__all__ = ["Config"]

LOG_LEVELS = {
    "critical": logging.CRITICAL,
    "error": logging.ERROR,
    "warning": logging.WARNING,
    "info": logging.INFO,
    "debug": logging.DEBUG,
}

here = os.getcwd()


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
        return json.dumps(self, indent=4)

    def __setitem__(self, key: str, value: typing.Any) -> None:
        key = key.upper()

        if isinstance(value, dict):
            if key in self.keys():
                for k, v in value.items():
                    super().__setitem__(k.upper(), v)
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


class Config(UpperDict, metaclass=Singleton):
    ENV: str
    DEBUG: bool
    APP: str
    HOST: str
    PORT: int
    LOG_LEVEL: str
    HOTRELOAD: bool
    AUTORELOAD: bool
    # template
    TEMPLATES: typing.Iterable[str]
    # url
    ALLOW_UNDERLINE: bool
    # middleware
    FORCE_SSL: bool
    ALLOWED_HOSTS: typing.Sequence[str]
    CORS_ALLOW_ORIGINS: typing.Sequence[str]
    CORS_ALLOW_METHODS: typing.Sequence[str]
    CORS_ALLOW_HEADERS: typing.Sequence[str]
    CORS_ALLOW_CREDENTIALS: bool
    CORS_ALLOW_ORIGIN_REGEX: typing.Optional[str]
    CORS_EXPOSE_HEADERS: typing.Sequence[str]
    CORS_MAX_AGE: int

    def setdefaults(self) -> None:
        """set default value"""

        self["env"] = "dev"
        self["debug"] = False
        self["app"] = "indexpy:app"
        self["host"] = "127.0.0.1"
        self["port"] = 4190
        self["log_level"] = "info"
        self["hotreload"] = False
        self["autoreload"] = True
        # template
        self["templates"] = ("templates",)
        # url
        self["allow_underline"] = False
        # middleware
        self["force_ssl"] = False
        self["allowed_hosts"] = ["*"]
        self["cors_allow_origins"] = ()
        self["cors_allow_methods"] = ("GET",)
        self["cors_allow_headers"] = ()
        self["cors_allow_credentials"] = False
        self["cors_allow_origin_regex"] = None
        self["cors_expose_headers"] = ()
        self["cors_max_age"] = 600

    def __init__(self) -> None:
        super().__init__({})
        self.setdefaults()
        # read config from file
        self.import_from_file()
        # read config from environ
        self.import_from_environ()

    def import_from_file(self) -> None:
        filename = None

        for _filename in ["index.json", "index.yaml", "index.yml"]:
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
            raise ConfigError(f"config must be a dictionary.")

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
        if name == f"_UpperDict__dict":
            return super().__setattr__(name, value)
        raise ConfigError("Modifying the attribute value of Config is not allowed.")

    def __delattr__(self, name: str) -> None:
        raise ConfigError("Modifying the attribute value of Config is not allowed.")

    def __delitem__(self, key: str) -> None:
        raise ConfigError("Modifying the attribute value of Config is not allowed.")

    def __setitem__(self, key: str, value: typing.Any) -> None:
        key = key.upper()

        if key == "DEBUG":
            value = bool(value)
        elif key == "PORT":
            value = int(value)
        elif key == "ALLOWED_HOSTS":
            value = list(value)
            value.append("testserver")

        super().__setitem__(key, value)

    def get(self, key, default=None) -> typing.Any:
        key = key.upper()
        env = super().get(self["env"].upper(), {})
        value = env.get(key, ...)
        if value is ...:
            value = super().get(key, default)
        return value
