import pytest

from indexpy.routing.routes import (
    Router,
    Routes,
    SubRoutes,
    HttpRoute,
    SocketRoute,
    NoMatchFound,
    NoRouteFound,
)
from indexpy.http import HTTPView
from indexpy.websocket import SocketView


@pytest.fixture
def router():
    def hello_world(request):
        return "hello world"

    def sayhi(request):
        return f"hi, {request.path_params['name']}"

    router = Router(
        Routes(
            HttpRoute("/sayhi/{name}", sayhi, "sayhi", method="get"),
            SubRoutes(
                "/hello",
                [
                    HttpRoute("/world", hello_world, "hello-world", method="get"),
                    SocketRoute("/socket_world", lambda websocket: None),
                ],
            ),
        )
    )

    @router.http("/about", name=None, method="get")
    @router.http("/about/{name}", method="get")
    def about(request):
        return str(request.url)

    @router.http("/http_view")
    class HTTP(HTTPView):
        pass

    @router.websocket("/socket_view", name="socket")
    class Socket(SocketView):
        pass

    return router


@pytest.mark.parametrize(
    "protocol,path,params",
    [
        ("http", "/hello/world", {}),
        ("http", "/sayhi/aber", {"name": "aber"}),
        ("http", "/about", {}),
        ("http", "/http_view", {}),
        ("websocket", "/socket_view", {}),
    ],
)
def test_router_success_search(router: Router, protocol, path, params):
    result = router.search(protocol, path)
    assert params == result[0]


@pytest.mark.parametrize(
    "protocol,path",
    [
        ("http", "/hello/world/"),
        ("http", "/sayhi/"),
        ("http", "/about/aber/"),
        ("http", "/http_view/123"),
        ("websocket", "/"),
        ("websocket", "/socket"),
        ("websocket", "/socket_view/"),
    ],
)
def test_router_fail_search(router: Router, protocol, path):
    with pytest.raises(NoMatchFound):
        router.search(protocol, path)


@pytest.mark.parametrize(
    "protocol,name,params,url",
    [
        ("http", "hello-world", {}, "/hello/world"),
        ("http", "sayhi", {"name": "aber"}, "/sayhi/aber"),
        ("http", "about", {"name": "aber"}, "/about/aber"),
        ("websocket", "socket", {}, "/socket_view"),
    ],
)
def test_router_success_url_for(router: Router, protocol, name, params, url):
    assert url == router.url_for(name, params, protocol)


def test_router_fail_url_for(router: Router):
    with pytest.raises(NoRouteFound):
        router.url_for("longlongname")
