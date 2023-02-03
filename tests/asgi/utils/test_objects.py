from __future__ import annotations

from xing.utils.objects import Singleton


def test_singleton():
    class S(metaclass=Singleton):
        pass

    assert S() is S()
