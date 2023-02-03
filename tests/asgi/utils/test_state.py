from __future__ import annotations

import pytest

from kui.utils import State


@pytest.mark.asyncio
async def test_state():
    state = State({"message": "hello world"})
    with state:
        assert state.message == "hello world"
        state.like = "you"
        assert state.like == "you"
        del state.like

    async with state:
        assert state.message == "hello world"

    assert state.get("like") is None
