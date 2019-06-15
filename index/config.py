import os
import json
import logging


__all__ = [
    "Config"
]

LOG_LEVELS = {
    "critical": logging.CRITICAL,
    "error": logging.ERROR,
    "warning": logging.WARNING,
    "info": logging.INFO,
    "debug": logging.DEBUG,
}


logger: logging.Logger = logging.getLogger("index")


class ConfigError(Exception):
    pass


class Singleton(type):
    """
    单例控制

    example:
        class Config(metaclass=Singleton):
            def __init__(self):
                pass

    """

    def __init__(self, *args, **kwargs):
        self.__instance = None
        super().__init__(*args, **kwargs)

    def __call__(self, *args, **kwargs):
        if self.__instance is None:
            self.__instance = super().__call__(*args, **kwargs)
            return self.__instance
        else:
            return self.__instance


class UpperDict:

    def __init__(self, data: dict):
        self.__dict = dict()
        for key in data.keys():
            self[key] = data[key]

    def __repr__(self):
        indent = 4
        result = ["{"]

        def append(line):
            result.append(" "*indent + line)

        for key, value in self.__dict.items():
            if isinstance(value, UpperDict):
                append(f"{key}: {{")
                for line in repr(value).splitlines()[1:-1]:
                    append(f"{line}")
                append("}")
            else:
                if isinstance(value, str):
                    append(f"{key}: '{value}',")
                else:
                    append(f"{key}: {value},")

        result.append("}")

        return "\n".join(result)

    def __str__(self):
        return self.__repr__()

    def __setitem__(self, key, value):
        key = key.upper()

        if isinstance(value, dict):
            self.__dict[key] = UpperDict(value)
        else:
            if key == "DEBUG":
                value = bool(value)
            elif key == "PORT":
                value = int(value)
            self.__dict[key] = value

    def __getitem__(self, key):
        return self.__dict[key.upper()]

    # def __setattr__(self, name, value):
    #     raise ConfigError("Modifying the attribute value of Config is not allowed.")

    def __getattr__(self, name):
        try:
            value = self.get(name)
            if value is None:
                raise KeyError()
            return value
        except KeyError:
            raise AttributeError(f"'{self.__class__.__name__}' object has no attribute '{name}'")

    def get(self, key, default=None):
        try:
            return self.__dict[key.upper()]
        except KeyError:
            return default


def _import_environ():
    result = {}
    for key in filter(
        lambda x: x.startswith("INDEX_"),
        os.environ.keys()
    ):
        result[key[6:]] = os.environ.get(key)
    return result


class Config(UpperDict, metaclass=Singleton):

    def __init__(self):
        super().__init__({})
        self.setdefault()
        self.update(_import_environ())
        self.import_from_file(os.path.join(self.path, "config.json"))

    @property
    def path(self):
        return os.getcwd()

    def import_from_file(self, jsonfile: str):
        try:
            with open(jsonfile, "r") as file:
                data = json.load(file)
            if not isinstance(data, dict):
                raise ConfigError(f"config must be a dictionary.")

            self.update(data)
        except FileNotFoundError:
            pass

    def setdefault(self):
        """set default value"""

        self["env"] = "dev"
        self["debug"] = False
        self["host"] = "127.0.0.1"
        self["port"] = 4190
        self['log_level'] = "info"

    def update(self, data: dict):
        for key in data.keys():
            self[key] = data[key]

    def get(self, key, default=None):
        env = super().get(self['env'], {})
        value = env.get(key, None)
        if value is None:
            value = super().get(key, default)
        return value


logging.basicConfig(
    format="%(asctime)s %(levelname)s: %(message)s",
    datefmt='%Y-%m-%d %H:%M:%S',
    level=LOG_LEVELS[Config().log_level]
)
logger.setLevel(LOG_LEVELS[Config().log_level])
