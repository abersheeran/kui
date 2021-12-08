from hintapi.utils.objects import Singleton


def test_singleton():
    class S(metaclass=Singleton):
        pass

    assert S() is S()
