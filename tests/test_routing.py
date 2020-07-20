import pytest

from indexpy.routing import RadixTree


@pytest.fixture
def tree():
    tree = RadixTree()

    tree.add("/hello", {"get": lambda x: x})
    tree.add("/hello/{name:str}", {"post": lambda x: x})
    tree.add("/sayhi/{name:str}", {"post": lambda x: x})

    return tree


@pytest.mark.parametrize(
    "path,params",
    [
        ("/hello", {}),
        ("/hello/aber", {"name": "aber"}),
        ("/sayhi/aber", {"name": "aber"}),
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
