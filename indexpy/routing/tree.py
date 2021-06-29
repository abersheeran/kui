from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any, Callable, Dict, Iterator, List, Optional, Pattern, Tuple
from typing import cast as typing_cast

from baize.routing import AnyConvertor, Convertor, compile_path

RouteType = Tuple[str, Dict[str, Convertor], Callable[[], Any]]


@dataclass
class TreeNode:
    characters: str
    re_pattern: Optional[Pattern] = None
    next_nodes: Optional[List[TreeNode]] = None

    route: Optional[RouteType] = None


def find_common_prefix(x: str, y: str) -> str:
    """
    find the longest common prefix of x and y
    """
    for i in range(min(len(x), len(y))):
        if x[i] != y[i]:
            return x[:i]
    return x[: i + 1]


def append(
    point: TreeNode, path_format: str, param_convertors: Dict[str, Convertor]
) -> TreeNode:
    """
    Construct the node corresponding to the specified path and return.

    The order of child nodes under the same node is determined by the order of addition.
    """
    if not path_format:
        return point

    if point.next_nodes is None:
        point.next_nodes = list()

    matched = re.match(r"^{\w+}", path_format)

    if matched is not None:
        length = matched.end()
        param_name = path_format[1 : length - 1]
        convertor = param_convertors[param_name]
        re_pattern = re.compile(convertor.regex)
        if isinstance(convertor, AnyConvertor) and path_format[-1] != "}":
            raise ValueError(
                "`AnyConvertor` is only allowed to appear at the end of path"
            )
        for node in (
            node for node in point.next_nodes or () if node.re_pattern is not None
        ):
            if (node.re_pattern == re_pattern) != (node.characters == param_name):
                raise ValueError(
                    "The same regular matching is used in the same position"
                    + ", but the parameter names are different."
                )
            if node.characters == param_name:
                return append(node, path_format[length:], param_convertors)

        new_node = TreeNode(characters=param_name, re_pattern=re_pattern)
        point.next_nodes.insert(0, new_node)
        return append(new_node, path_format[length:], param_convertors)
    else:
        length = path_format.find("{")
        if length == -1:
            length = len(path_format)

        for node in (
            node for node in point.next_nodes or () if node.re_pattern is None
        ):
            prefix = find_common_prefix(node.characters, path_format[:length])
            if prefix == "":
                continue
            if node.characters == prefix:
                return append(node, path_format[len(prefix) :], param_convertors)

            node_index = point.next_nodes.index(node)
            prefix_node = TreeNode(characters=prefix, next_nodes=[])
            point.next_nodes[node_index] = prefix_node
            node.characters = node.characters[len(prefix) :]
            typing_cast(List[TreeNode], prefix_node.next_nodes).insert(0, node)
            if path_format[:length] == prefix:
                return append(prefix_node, path_format[length:], param_convertors)

            new_node = TreeNode(characters=path_format[len(prefix) : length])
            typing_cast(List[TreeNode], prefix_node.next_nodes).insert(0, new_node)
            return append(new_node, path_format[length:], param_convertors)

        new_node = TreeNode(characters=path_format[:length])
        point.next_nodes.insert(0, new_node)
        return append(new_node, path_format[length:], param_convertors)


class RadixTree:
    def __init__(self) -> None:
        self.root = TreeNode("/")

    def append(self, path: str, endpoint: Callable) -> None:
        if path[0] != "/":
            raise ValueError('path must start with "/"')
        path_format, param_convertors = compile_path(path)
        if path_format == path and self.search(path) != (None, None):
            raise ValueError(
                f"This constant route {path} can be matched by the added routes."
            )
        point = append(self.root, path_format[1:], param_convertors)

        if point.route is not None:
            raise ValueError(f"Routing conflict: {path}")

        point.route = (path_format, param_convertors, endpoint)

    def search(self, path: str) -> Tuple[Dict[str, Any], Callable] | Tuple[None, None]:
        stack: List[Tuple[str, TreeNode]] = [(path, self.root)]
        params: Dict[str, Any] = {}

        while stack:
            path, point = stack.pop()

            if point.re_pattern is None:
                if not path.startswith(point.characters):
                    continue
                length = len(point.characters)
            else:
                none_or_match = re.match(point.re_pattern, path)
                if none_or_match is None:
                    continue
                result = none_or_match.group()
                params[point.characters] = result
                length = len(result)

            if length == len(path):  # found the first suitable route
                if point.route is None:
                    return None, None
                else:
                    _, param_convertors, endpoint = point.route
                    return (
                        {
                            name: param_convertors[name].to_python(value)
                            for name, value in params.items()
                            if name in param_convertors
                        },
                        endpoint,
                    )

            path = path[length:]
            for node in point.next_nodes or ():
                stack.append((path, node))

        return None, None

    def iterator(self) -> Iterator[Tuple[str, Callable]]:
        stack: List[TreeNode] = [self.root]

        while stack:
            point = stack.pop()
            for node in point.next_nodes or ():
                stack.append(node)
            if point.route is None:
                continue
            path_format, _, endpoint = point.route
            yield path_format, endpoint
