import re
import typing
from dataclasses import dataclass, field

from .convertors import Convertor, PathConvertor, compile_path


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
                        if path_format[left:right] == prefix:
                            point = prefix_node
                        else:
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
