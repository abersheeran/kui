from httpx import Client

from hintapi import HttpRoute
from hintapi.routing.extensions import MultimethodRoutes as Routes


def test_routes():
    routes = Routes()
    routes << Routes(
        HttpRoute("/login", test_mulitmethodroutes),
        HttpRoute("/register", test_mulitmethodroutes),
    )
    routes == Routes(
        HttpRoute("/login", test_mulitmethodroutes),
        HttpRoute("/register", test_mulitmethodroutes),
    )

    (
        routes
        << Routes(
            HttpRoute("/t/login", test_mulitmethodroutes),
            HttpRoute("/t/register", test_mulitmethodroutes),
        )
    ) == (
        Routes(
            HttpRoute("/login", test_mulitmethodroutes),
            HttpRoute("/register", test_mulitmethodroutes),
        )
        + Routes(
            HttpRoute("/t/login", test_mulitmethodroutes),
            HttpRoute("/t/register", test_mulitmethodroutes),
        )
    )


def test_mulitmethodroutes():
    from hintapi import HintAPI

    routes = Routes()

    @routes.http.get("/user")
    def list_user():
        pass

    @routes.http.post("/user")
    def create_user():
        pass

    @routes.http.delete("/user")
    def delete_user():
        pass

    app = HintAPI(routes=routes)

    endpoint = app.router.search("http", "/user")[1]
    assert issubclass(endpoint, routes.base_class)
    assert hasattr(endpoint, "__methods__")
    assert (
        hasattr(endpoint, "get")
        and hasattr(endpoint, "post")
        and hasattr(endpoint, "delete")
    )


def test_mulitmethodroutes_with_prefix():
    from hintapi import HintAPI

    routes = Routes()

    @routes.http.get("/user")
    def list_user():
        pass

    @routes.http.post("/user")
    def create_user():
        pass

    @routes.http.delete("/user")
    def delete_user():
        pass

    app = HintAPI(routes="/api" // routes)

    endpoint = app.router.search("http", "/api/user")[1]
    assert issubclass(endpoint, routes.base_class)
    assert hasattr(endpoint, "__methods__")
    assert (
        hasattr(endpoint, "get")
        and hasattr(endpoint, "post")
        and hasattr(endpoint, "delete")
    )


def test_mulitmethodroutes_with_parameters():
    from hintapi import HintAPI, Path

    routes = Routes()

    @routes.http.get("/{name}", name=None)
    @routes.http.post("/{name}", name=None)
    @routes.http.put("/{name}", name=None)
    @routes.http.patch("/{name}", name=None)
    @routes.http.delete("/{name}", name=None)
    def name(name: str = Path(...)):
        return name

    app = HintAPI(routes=routes)

    with Client(app=app, base_url="http://localhost") as client:
        resp = client.get("/aber")
        assert resp.text == "aber"

        resp = client.get("/")
        assert resp.status_code == 404
