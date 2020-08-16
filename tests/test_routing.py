from decimal import Decimal
from uuid import UUID
import pytest

from indexpy.routing.tree import RadixTree
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
def tree():
    tree = RadixTree()

    tree.append("/hello/{time:int}", ...)
    tree.append("/hello", ...)
    tree.append("/hello/world", ...)
    tree.append("/sayhi/{name}", ...)
    tree.append("/sayhi/{name}/suffix", ...)
    tree.append("/sayhi/{name}/avatar.{suffix}", ...)
    tree.append("/path/{filepath:path}", ...)
    tree.append("/decimal/{number:decimal}", ...)
    tree.append("/uuid/{id:uuid}", ...)

    return tree


@pytest.mark.parametrize(
    "path,params",
    [
        ("/hello", {}),
        ("/hello/world", {}),
        ("/hello/123", {"time": 123}),
        ("/sayhi/aber", {"name": "aber"}),
        ("/sayhi/aber/suffix", {"name": "aber"}),
        ("/sayhi/aber/avatar.png", {"name": "aber", "suffix": "png"}),
        ("/path/adsf", {"filepath": "adsf"}),
        ("/path/adsf/123", {"filepath": "adsf/123"}),
        ("/decimal/1.111", {"number": Decimal("1.111")}),
        (
            "/uuid/123e4567-e89b-12d3-a456-426655440000",
            {"id": UUID("123e4567-e89b-12d3-a456-426655440000")},
        ),
    ],
)
def test_tree_success_search(tree: RadixTree, path, params):
    result = tree.search(path)
    assert result is not None
    raw_params, node = result
    assert {
        key: node.param_convertors[key].convert(value)
        for key, value in raw_params.items()
    } == params


@pytest.mark.parametrize(
    "path", ["", "/hello/", "/hello/world/", "/sayhi/aber/avatar"],
)
def test_tree_fail_search(tree: RadixTree, path):
    assert tree.search(path)[0] is None, f"error in {path}"


@pytest.mark.parametrize(
    "path",
    [
        "/path/{urlpath:path}/",
        "/sayhi/{name:int}/suffix",
        "/sayhi/{hi}/suffix",
        "/hello",
    ],
)
def test_tree_fail_add(tree: RadixTree, path):
    with pytest.raises(ValueError):
        tree.append(path, ...)


@pytest.fixture
def router():
    def hello_world(request):
        return "hello world"

    def sayhi(request):
        return f"hi, {request.path_params['name']}"

    router = Router(
        Routes(
            HttpRoute("/sayhi/{name}", sayhi, "sayhi", "get"),
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
    def about(request):
        return str(request.url)

    router.http("/about/{name}", about, method="get")

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
