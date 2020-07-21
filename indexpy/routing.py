import re
import math
import typing
import uuid
from decimal import Decimal
from functools import partial
from dataclasses import dataclass, field

from .types import Literal


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

    def to_string(self, value: Decimal) -> str:
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


@dataclass
class TreeNode:
    characters: str
    re_pattern: typing.Optional[typing.Pattern] = None
    param_convertors: typing.Dict[str, Convertor] = field(default_factory=dict)
    next_nodes: typing.List["TreeNode"] = field(default_factory=list)
    endpoint: typing.Any = None


def find_common_prefix(x: str, y: str) -> str:
    """
    find the longest common prefix of x and y
    """
    for i in range(min(len(x), len(y))):
        if x[i] != y[i]:
            return x[:i]
    return x[: i + 1]


class RadixTree:
    def __init__(self) -> None:
        self.root = TreeNode("/")

    def append(self, path: str, endpoint: typing.Any = None) -> None:
        point = self.root
        path_format, param_convertors = compile_path(path)

        left, path_format_len = 1, len(path_format)

        while left < path_format_len:

            if path_format[left] == "{":
                right = path_format.find("}", left) + 1
                param_name = path_format[left + 1 : right - 1]
                convertor = param_convertors[param_name]
                re_pattern = re.compile(convertor.regex)
                if isinstance(convertor, PathConvertor) and right < path_format_len:
                    raise ValueError(
                        "`PathConvertor` is only allowed to appear at the end of path"
                    )

                for node in filter(
                    lambda node: node.re_pattern is not None, point.next_nodes
                ):
                    if (node.re_pattern == re_pattern) != (
                        node.characters == param_name
                    ):
                        raise ValueError(
                            "The same regular matching is used in the same position"
                            + ", but the parameter names are different."
                        )
                    if node.characters == param_name:
                        point = node
                        break
                else:
                    new_node = TreeNode(characters=param_name, re_pattern=re_pattern)
                    point.next_nodes.append(new_node)
                    point = new_node

                left = right
            else:
                right = path_format.find("{", left)
                if right == -1:
                    right = path_format_len

                for node in filter(
                    lambda node: node.re_pattern is None, point.next_nodes
                ):
                    prefix = find_common_prefix(
                        node.characters, path_format[left:right]
                    )
                    if prefix == "":
                        continue
                    elif node.characters == prefix:
                        point = node
                        right = left + len(prefix)
                        break
                    else:
                        node_index = point.next_nodes.index(node)
                        prefix_node = TreeNode(characters=prefix)
                        point.next_nodes[node_index] = prefix_node
                        node.characters = node.characters[len(prefix) :]
                        prefix_node.next_nodes.append(node)
                        new_node = TreeNode(
                            characters=path_format[left + len(prefix) : right]
                        )
                        prefix_node.next_nodes.append(new_node)
                        point = new_node
                        break
                else:
                    new_node = TreeNode(characters=path_format[left:right])
                    point.next_nodes.append(new_node)
                    point = new_node

                left = right

        if point.endpoint is not None:
            raise ValueError(f"Routing conflict: {path}")

        point.endpoint = endpoint
        point.param_convertors = param_convertors

    def search(
        self, path: str
    ) -> typing.Union[
        typing.Tuple[typing.Dict[str, typing.Any], TreeNode], typing.Tuple[None, None]
    ]:
        point = self.root
        params = {}

        left, path_len = 1, len(path)
        while left < path_len:
            for node in point.next_nodes:
                if node.re_pattern is not None:
                    none_or_match = re.match(node.re_pattern, path[left:])
                    if none_or_match:
                        result = none_or_match.group()
                        params[node.characters] = result
                        point = node
                        left += len(result)
                        break
                else:
                    right = left + len(node.characters)
                    if path[left:right] == node.characters:
                        point = node
                        left = right
                        break
            else:
                return None, None

        if left == path_len and point.endpoint is not None:
            return params, point
        return None, None


class NoMatchFound(Exception):
    """
    Raised by `.search(path)` if no matching route exists.
    """


class NoRouteFound(Exception):
    """
    Raised by `.url_for(name, **path_params)` if no matching route exists.
    """


@dataclass
class BaseRoute:
    path: str
    endpoint: typing.Any
    name: str


@dataclass
class HttpRoute(BaseRoute):
    name: str = ""


@dataclass
class SocketRoute(BaseRoute):
    name: str = ""


class Routes(typing.List[BaseRoute]):
    def __init__(self, *iterable: typing.Union["BaseRoute", "Mount"]) -> None:
        routes = []
        for route_or_mount in iterable:
            if not isinstance(route_or_mount, Mount):
                routes.append(route_or_mount)
                continue
            for route in route_or_mount:  # type: BaseRoute
                routes.append(
                    route.__class__(
                        path=route_or_mount.prefix + route.path,
                        endpoint=route.endpoint,
                        name=route.name,
                    )
                )
        super().__init__(routes)

    def http(
        self, path: str, endpoint: typing.Any = None, *, name: str = ""
    ) -> typing.Any:
        """
        shortcut for `self.append`

        example:
            @router.http("/path", name="endpoint-name")
            async def endpoint(request): ...
        or
            router.http("/path", endpoint, name="endpoint-name")
        """
        if path and endpoint is None:
            # example: @router.http("/path", name="hello")
            #          async def func(request): ...
            return partial(
                lambda endpoint: self.http(path=path, endpoint=endpoint, name=name)
            )

        if endpoint is None:
            raise ValueError("endpoint must be is not None")

        if name == "":
            name = endpoint.__name__

        self.append(HttpRoute(path, endpoint, name))

        return endpoint

    def websocket(
        self, path: str, endpoint: typing.Any = None, *, name: str = ""
    ) -> typing.Any:
        """
        shortcut for `self.append`

        example:
            @router.websocket("/path", name="endpoint-name")
            async def endpoint(websocket): ...
        or
            router.websocket("/path", endpoint, name="endpoint-name")
        """
        if path and endpoint is None:
            # example: @router.websocket("/path", name="hello")
            #          async def func(websocket): ...
            return partial(
                lambda endpoint: self.websocket(path=path, endpoint=endpoint, name=name)
            )

        if endpoint is None:
            raise ValueError("endpoint must be is not None")

        if name == "":
            name = endpoint.__name__

        self.append(SocketRoute(path, endpoint, name))

        return endpoint


class Mount(Routes):
    def __init__(self, prefix: str, routes: Routes = []) -> None:
        self.prefix = prefix
        super().__init__(*routes)


class Router:
    def __init__(self, routes: typing.List[BaseRoute] = list()) -> None:
        self.http_tree = RadixTree()
        self.websocket_tree = RadixTree()

        self.http_routes: typing.Dict[
            str, typing.Tuple[str, typing.Dict[str, Convertor], typing.Any]
        ] = {}
        self.websocket_routes: typing.Dict[
            str, typing.Tuple[str, typing.Dict[str, Convertor], typing.Any]
        ] = {}

        for route in routes:
            if isinstance(route, HttpRoute):
                self.append("http", route.path, route.endpoint, route.name)
            elif isinstance(route, SocketRoute):
                self.append("websocket", route.path, route.endpoint, route.name)
            else:
                raise TypeError(
                    f"Need type: `HttpRoute` or `SocketRoute`, but got type: {type(route)}"
                )

    def append(
        self,
        protocol: Literal["http", "websocket"],
        path: str,
        endpoint: typing.Any,
        name: str = None,
    ) -> None:

        if endpoint is None:
            raise ValueError("endpoint must be not None")

        if protocol == "http":
            radix_tree = self.http_tree
            routes = self.http_routes
        elif protocol == "websocket":
            radix_tree = self.websocket_tree
            routes = self.websocket_routes
        else:
            raise ValueError("`protocol` must be in ('http', 'websocket')")

        radix_tree.append(path, endpoint)
        path_format, path_convertors = compile_path(path)

        if name in routes:
            raise ValueError(f"Duplicate route name: {name}")
        if isinstance(name, str) and name:
            routes[name] = (path_format, path_convertors, endpoint)

    def search(
        self, protocol: Literal["http", "websocket"], path: str
    ) -> typing.Tuple[typing.Dict[str, typing.Any], typing.Any]:
        if protocol == "http":
            radix_tree = self.http_tree
        elif protocol == "websocket":
            radix_tree = self.websocket_tree
        else:
            raise ValueError("`protocol` must be in ('http', 'websocket')")

        params, node = radix_tree.search(path)

        if params is None or node is None:
            raise NoMatchFound(path)

        return (
            {
                name: node.param_convertors[name].to_string(value)
                for name, value in params.items()
            },
            node.endpoint,
        )

    def url_for(
        self,
        name: str,
        path_params: typing.Dict[str, typing.Any] = {},
        protocol: Literal["http", "websocket"] = "http",
    ) -> str:
        if protocol == "http":
            routes = self.http_routes
        elif protocol == "websocket":
            routes = self.websocket_routes
        else:
            raise ValueError("`protocol` must be in ('http', 'websocket')")

        if name not in routes:
            raise NoRouteFound(f"No route with name '{name}' exists")

        path_format, path_convertors, _ = routes[name]

        return path_format.format_map(
            {
                name: path_convertors[name].to_string(value)
                for name, value in path_params.items()
            }
        )

    def http(
        self, path: str, endpoint: typing.Any = None, *, name: str = ""
    ) -> typing.Any:
        """
        shortcut for `self.append`

        example:
            @router.http("/path", name="endpoint-name")
            async def endpoint(request): ...
        or
            router.http("/path", endpoint, name="endpoint-name")
        """
        if path and endpoint is None:
            # example: @router.http("/path", name="hello")
            #          async def func(request): ...
            return partial(
                lambda endpoint: self.http(path=path, endpoint=endpoint, name=name)
            )

        if endpoint is None:
            raise ValueError("endpoint must be is not None")

        if name == "":
            name = endpoint.__name__

        self.append("http", path, endpoint, name)

        return endpoint

    def websocket(
        self, path: str, endpoint: typing.Any = None, *, name: str = ""
    ) -> typing.Any:
        """
        shortcut for `self.append`

        example:
            @router.websocket("/path", name="endpoint-name")
            async def endpoint(websocket): ...
        or
            router.websocket("/path", endpoint, name="endpoint-name")
        """
        if path and endpoint is None:
            # example: @router.websocket("/path", name="hello")
            #          async def func(websocket): ...
            return partial(
                lambda endpoint: self.websocket(path=path, endpoint=endpoint, name=name)
            )

        if endpoint is None:
            raise ValueError("endpoint must be is not None")

        if name == "":
            name = endpoint.__name__

        self.append("websocket", path, endpoint, name)

        return endpoint
