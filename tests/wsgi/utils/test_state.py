from hintapi.utils import State


def test_state():
    state = State({"message": "hello world"})
    with state:
        assert state.message == "hello world"
        state.like = "you"
        assert state.like == "you"
        del state.like

    with state:
        assert state.message == "hello world"

    assert state.get("like") is None
