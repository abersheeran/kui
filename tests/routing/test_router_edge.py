import pytest

from kui.asgi import HttpRoute, Kui, Routes, SocketRoute


def test_duplicate_route_name_raises():
    app = Kui()

    app.router <<= HttpRoute("/a", lambda: "a", name="dup")

    with pytest.raises(ValueError, match="Duplicate route name: dup"):
        app.router <<= HttpRoute("/b", lambda: "b", name="dup")


def test_search_invalid_protocol_raises():
    app = Kui()

    app.router <<= HttpRoute("/", lambda: "ok")

    with pytest.raises(ValueError, match="`protocol` must be in"):
        app.router.search("ftp", "/")  # type: ignore[arg-type]


def test_routes_radd_preserves_order():
    left = [HttpRoute("/a", lambda: "a"), SocketRoute("/ws", lambda: None)]
    right = Routes(HttpRoute("/b", lambda: "b"))

    combined = right.__radd__(left)

    assert [route.path for route in combined] == ["/a", "/ws", "/b"]
