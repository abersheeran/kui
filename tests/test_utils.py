from indexpy.utils import Singleton, State, import_module


def test_singleton():
    class S(metaclass=Singleton):
        pass

    assert S() is S()


def test_import_module():
    assert import_module("commands")
    assert import_module("sys") is None


def test_state():
    state = State({"message": "hello world"})
    with state:
        assert state.message == "hello world"
        state.like = "you"
        assert state.like == "you"
        del state.like
    assert state.get("like") is None
