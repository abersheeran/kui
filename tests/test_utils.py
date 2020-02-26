from indexpy.utils import Singleton, import_module


def test_singleton():
    class S(metaclass=Singleton):
        pass

    assert S() is S()


def test_import_module():
    assert import_module("commands")
    assert import_module("sys") is None
