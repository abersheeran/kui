import re
from typing import Optional, Union, Dict, List, Tuple, Pattern, Any
from dataclasses import dataclass, field

from ..types import ASGIApp
from .convertors import Convertor, PathConvertor, compile_path


@dataclass
class TreeNode:
    characters: str
    re_pattern: Optional[Pattern] = None
    param_convertors: Dict[str, Convertor] = field(default_factory=dict)
    next_nodes: List["TreeNode"] = field(default_factory=list)
    endpoint: Optional[ASGIApp] = None


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

    if path_format[0] == "{":
        length = path_format.find("}") + 1
        param_name = path_format[1 : length - 1]
        convertor = param_convertors[param_name]
        re_pattern = re.compile(convertor.regex)
        if isinstance(convertor, PathConvertor) and path_format[-1] != "}":
            raise ValueError(
                "`PathConvertor` is only allowed to appear at the end of path"
            )
        for node in filter(lambda node: node.re_pattern is not None, point.next_nodes):
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

    length = path_format.find("{")
    if length == -1:
        length = len(path_format)

    for node in filter(lambda node: node.re_pattern is None, point.next_nodes):
        prefix = find_common_prefix(node.characters, path_format[:length])
        if prefix == "":
            continue
        if node.characters == prefix:
            return append(node, path_format[len(prefix) :], param_convertors)

        node_index = point.next_nodes.index(node)
        prefix_node = TreeNode(characters=prefix)
        point.next_nodes[node_index] = prefix_node
        node.characters = node.characters[len(prefix) :]
        prefix_node.next_nodes.insert(0, node)
        if path_format[:length] == prefix:
            return append(prefix_node, path_format[length:], param_convertors)

        new_node = TreeNode(characters=path_format[len(prefix) : length])
        prefix_node.next_nodes.insert(0, new_node)
        return append(new_node, path_format[length:], param_convertors)

    new_node = TreeNode(characters=path_format[:length])
    point.next_nodes.insert(0, new_node)
    return append(new_node, path_format[length:], param_convertors)


def search(
    point: TreeNode, path: str, params: Dict[str, str]
) -> Optional[Tuple[Dict[str, str], TreeNode]]:
    """
    Find a suitable route
    """
    stack: List[Tuple[str, TreeNode]] = [(path, point)]

    while stack:
        path, point = stack.pop(len(stack) - 1)

        if point.re_pattern is None:
            length = len(point.characters)
            if path[:length] != point.characters:
                continue
        else:
            none_or_match = re.match(point.re_pattern, path)
            if none_or_match is None:
                continue
            result = none_or_match.group()
            params[point.characters] = result
            length = len(result)

        path = path[length:]
        if not path:  # path == "", found the first suitable route
            for name in set(params.keys()) - set(point.param_convertors.keys()):
                del params[name]
            return params, point

        for node in point.next_nodes:
            stack.append((path, node))

    return None


class RadixTree:
    def __init__(self) -> None:
        self.root = TreeNode("/")

    def append(self, path: str, endpoint: ASGIApp) -> None:
        if path[0] != "/":
            raise ValueError('path must start with "/"')
        path_format, param_convertors = compile_path(path)
        point = append(self.root, path_format[1:], param_convertors)

        if point.endpoint is not None:
            raise ValueError(f"Routing conflict: {path}")

        point.endpoint = endpoint
        point.param_convertors = param_convertors

    def search(
        self, path: str
    ) -> Union[Tuple[Dict[str, Any], ASGIApp], Tuple[None, None]]:
        result = search(self.root, path, {})
        if result is None:
            return None, None

        raw_params, node = result
        if node.endpoint is None:
            return None, None

        return (
            {
                name: node.param_convertors[name].convert(value)
                for name, value in raw_params.items()
            },
            node.endpoint,
        )
