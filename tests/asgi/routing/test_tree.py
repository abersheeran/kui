from __future__ import annotations

from decimal import Decimal
from uuid import UUID

import pytest

from kui.routing.tree import RadixTree


@pytest.fixture
def tree():
    tree = RadixTree()

    tree.append("/hello/{time:int}", ...)
    tree.append("/hello", ...)
    tree.append("/hello/world", ...)
    tree.append("/sayhi/{name}", ...)
    tree.append("/sayhi/{name}/suffix", ...)
    tree.append("/sayhi/{name}/avatar.{suffix}", ...)
    tree.append("/path/{filepath:any}", ...)
    tree.append("/decimal/{number:decimal}", ...)
    tree.append("/uuid/{id:uuid}", ...)

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
        ("/path/adsf", {"filepath": "adsf"}),
        ("/path/adsf/123", {"filepath": "adsf/123"}),
        ("/decimal/1.111", {"number": Decimal("1.111")}),
        (
            "/uuid/123e4567-e89b-12d3-a456-426655440000",
            {"id": UUID("123e4567-e89b-12d3-a456-426655440000")},
        ),
    ],
)
def test_tree_success_search(tree: RadixTree, path, params):
    result = tree.search(path)
    assert result is not None
    params, node = result
    assert params == params


@pytest.mark.parametrize(
    "path",
    ["", "/hello/", "/hello/world/", "/sayhi/aber/avatar"],
)
def test_tree_fail_search(tree: RadixTree, path):
    assert tree.search(path)[0] is None, f"error in {path}"


@pytest.mark.parametrize(
    "path",
    [
        "/path/{urlpath:any}/",
        "/sayhi/{name:int}/suffix",
        "/sayhi/{hi}/suffix",
        "/sayhi/aber",
        "/hello/{time:int}",
        "a",
        "/static/{filename}.py",
    ],
)
def test_tree_fail_add(tree, path):
    with pytest.raises(ValueError):
        tree.append(path, ...)


def test_tree_iterator(tree: RadixTree):
    for _0, _1 in zip(
        tree.iterator(),
        [
            ("/hello", ...),
            ("/hello/{time}", ...),
            ("/hello/world", ...),
            ("/sayhi/{name}", ...),
            ("/sayhi/{name}/suffix", ...),
            ("/sayhi/{name}/avatar.{suffix}", ...),
            ("/path/{filepath}", ...),
            ("/decimal/{number}", ...),
            ("/uuid/{id}", ...),
        ],
    ):
        assert _0 == _1
