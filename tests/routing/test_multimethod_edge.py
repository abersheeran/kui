import pytest

from kui.asgi import HttpView, SocketRoute
from kui.asgi import MultimethodRoutes as Routes


def test_multimethod_rejects_class_view():
    routes = Routes(base_class=HttpView)

    with pytest.raises(
        TypeError, match=r"MultimethodRoutes not allow use class-base view\."
    ):

        @routes.http("/path")
        class MyView(HttpView):
            @classmethod
            async def get(cls):
                return "ok"


def test_multimethod_allows_socket_route():
    routes = Routes(base_class=HttpView)

    async def websocket_endpoint():
        return None

    routes <<= SocketRoute("/ws", websocket_endpoint)

    assert len(routes) == 1
    assert routes[0].path == "/ws"
