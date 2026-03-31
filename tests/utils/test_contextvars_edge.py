from contextvars import ContextVar

from kui.utils.contextvars import bind_contextvar


class DummyObj:
    pass


def test_contextvar_bind_setattr():
    var = ContextVar("test")
    bound = bind_contextvar(var)
    obj = DummyObj()
    var.set(obj)

    bound.name = "hello"

    assert obj.name == "hello"


def test_contextvar_bind_delattr():
    var = ContextVar("test")
    bound = bind_contextvar(var)
    obj = DummyObj()
    obj.name = "hello"
    var.set(obj)

    del bound.name

    assert not hasattr(obj, "name")


def test_contextvar_bind_getitem():
    var = ContextVar("test")
    bound = bind_contextvar(var)
    var.set({"key": "value"})

    assert bound["key"] == "value"


def test_contextvar_bind_setitem():
    var = ContextVar("test")
    bound = bind_contextvar(var)
    data = {}
    var.set(data)

    bound["key"] = "value"

    assert data["key"] == "value"


def test_contextvar_bind_delitem():
    var = ContextVar("test")
    bound = bind_contextvar(var)
    data = {"key": "value"}
    var.set(data)

    del bound["key"]

    assert "key" not in data
