from __future__ import annotations

import pytest

from kui.openapi.extra_docs import merge_openapi_info


@pytest.mark.parametrize(
    "f,s,r",
    [
        ({"a": 1}, {"b": 1}, {"a": 1, "b": 1}),
        ({"a": {"a": 1}, "b": 1}, {"a": {"b": 1}}, {"a": {"a": 1, "b": 1}, "b": 1}),
        ({"a": (1, 2)}, {"a": (3,)}, {"a": [1, 2, 3]}),
    ],
)
def test_merge_openapi_info(f, s, r):
    assert merge_openapi_info(f, s) == r
