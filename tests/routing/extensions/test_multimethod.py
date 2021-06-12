from indexpy import HttpRoute
from indexpy.routing.extensions import MultimethodRoutes as Routes


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
    from indexpy import Index

    routes = Routes()

    @routes.http.get("/user")
    async def list_user():
        pass

    @routes.http.post("/user")
    async def create_user():
        pass

    @routes.http.delete("/user")
    async def delete_user():
        pass

    app = Index()
    app.router << "/test" // routes

    endpoint = app.router.search("http", "/test/user")[1]
    assert issubclass(endpoint, routes.base_class)
    assert hasattr(endpoint, "__methods__")
    assert (
        hasattr(endpoint, "get")
        and hasattr(endpoint, "post")
        and hasattr(endpoint, "delete")
    )
