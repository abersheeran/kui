import pytest

from kui.asgi import HttpRoute, Routes, SocketRoute
from kui.asgi.routing import Router


def test_http_middleware_after_route_raises():
    routes = Routes(HttpRoute("/a", lambda: "a"))

    with pytest.raises(RuntimeError, match="Can not append middleware after route"):

        @routes.http_middleware
        def middleware(endpoint):
            return endpoint


def test_socket_middleware_after_route_raises():
    routes = Routes(SocketRoute("/ws", lambda: None))

    with pytest.raises(RuntimeError, match="Can not append middleware after route"):

        @routes.socket_middleware
        def middleware(endpoint):
            return endpoint


def test_http_middleware_before_routes_ok():
    routes = Routes()

    @routes.http_middleware
    def middleware(endpoint):
        return endpoint

    @routes.http.get("/")
    async def handler():
        return "ok"

    assert len(routes) == 1
    assert routes[0].path == "/"
    assert handler.__name__ == "handler"


def test_append_invalid_route_type_raises():
    router = Router([])

    with pytest.raises(TypeError, match="Need type"):
        router.append("not a route")
