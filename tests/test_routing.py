import pytest

from indexpy.routing import RadixTree


@pytest.fixture
def tree():
    tree = RadixTree()

    tree.add("/hello")
    tree.add("/hello/{time:int}")
    tree.add("/hello/world")
    tree.add("/sayhi/{name}")
    tree.add("/sayhi/{name}/suffix")
    tree.add("/sayhi/{name}/avatar.{suffix}")

    return tree


@pytest.mark.parametrize(
    "path,params",
    [
        ("/hello", {}),
        ("/hello/world", {}),
        ("/hello/123", {"time": 123}),
        ("/sayhi/aber", {"name": "aber"}),
        ("/sayhi/aber/suffix", {"name": "aber"}),
        ("/sayhi/aber/avatar.png", {"name": "aber", "suffix": "png"}),
    ],
)
def test_tree_success_search(tree: RadixTree, path, params):
    result = tree.search(path)
    assert result is not None
    raw_params, node = result
    assert {
        key: node.param_convertors[key].convert(value)
        for key, value in raw_params.items()
    } == params
