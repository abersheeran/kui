import math
import re
import typing
import uuid
from decimal import Decimal


class Convertor:
    regex = ""

    def convert(self, value: str) -> typing.Any:
        raise NotImplementedError()

    def to_string(self, value: typing.Any) -> str:
        raise NotImplementedError()


class StringConvertor(Convertor):
    regex = "[^/]+"

    def convert(self, value: str) -> str:
        return value

    def to_string(self, value: typing.Any) -> str:
        value = str(value)
        if not value:
            raise ValueError("Must not be empty")
        if "/" in value:
            raise ValueError("May not contain path separators")
        return value


class PathConvertor(Convertor):
    regex = ".*"

    def convert(self, value: str) -> str:
        return str(value)

    def to_string(self, value: typing.Any) -> str:
        return str(value)


class IntegerConvertor(Convertor):
    regex = "[0-9]+"

    def convert(self, value: str) -> int:
        return int(value)

    def to_string(self, value: typing.Any) -> str:
        value = int(value)
        if value < 0:
            raise ValueError("Negative integers are not supported")
        return str(value)


class DecimalConvertor(Convertor):
    regex = "[0-9]+(.[0-9]+)?"

    def convert(self, value: str) -> Decimal:
        return Decimal(value)

    def to_string(self, value: typing.Any) -> str:
        value = Decimal(value)
        if value < Decimal("0.0"):
            raise ValueError("Negative decimal are not supported")
        if math.isnan(value):
            raise ValueError("NaN values are not supported")
        if math.isinf(value):
            raise ValueError("Infinite values are not supported")
        return str(value).rstrip("0").rstrip(".")


class UUIDConvertor(Convertor):
    regex = "[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}"

    def convert(self, value: str) -> uuid.UUID:
        return uuid.UUID(value)

    def to_string(self, value: uuid.UUID) -> str:
        return str(value)


CONVERTOR_TYPES = {
    "str": StringConvertor(),
    "path": PathConvertor(),
    "int": IntegerConvertor(),
    "decimal": DecimalConvertor(),
    "uuid": UUIDConvertor(),
}

# Match parameters in URL paths, eg. '{param}', and '{param:int}'
PARAM_REGEX = re.compile(r"{([a-zA-Z_][a-zA-Z0-9_]*)(:[a-zA-Z_][a-zA-Z0-9_]*)?}")


def is_compliant(path: str) -> bool:
    """
    Whether the "{...}" are closed
    """
    unclosed_count = 0
    for c in path:
        if c == "{":
            unclosed_count += 1
        elif c == "}":
            unclosed_count -= 1
        # count("}") > count("{")
        if unclosed_count < 0:
            return False
    return unclosed_count == 0


def compile_path(path: str) -> typing.Tuple[str, typing.Dict[str, Convertor]]:
    """
    Given a path string, like: "/{username:str}", return a two-tuple
    of (format, {param_name:convertor}).

    format:     "/{username}"
    convertors: {"username": StringConvertor()}
    """
    if not is_compliant(path):
        raise ValueError(f"There are unclosed braces: {path}")

    path_format = ""

    idx = 0
    param_convertors = {}
    for match in PARAM_REGEX.finditer(path):
        param_name, convertor_type = match.groups("str")
        convertor_type = convertor_type.lstrip(":")
        if convertor_type not in CONVERTOR_TYPES:
            raise ValueError(f"Unknown path convertor '{convertor_type}'")
        convertor = CONVERTOR_TYPES[convertor_type]

        path_format += path[idx : match.start()]
        path_format += "{%s}" % param_name

        param_convertors[param_name] = convertor

        idx = match.end()

    path_format += path[idx:]

    return path_format, param_convertors
