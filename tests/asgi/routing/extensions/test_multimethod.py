import pytest
from async_asgi_testclient import TestClient

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

    app = Index(routes=routes)

    endpoint = app.router.search("http", "/user")[1]
    assert issubclass(endpoint, routes.base_class)
    assert hasattr(endpoint, "__methods__")
    assert (
        hasattr(endpoint, "get")
        and hasattr(endpoint, "post")
        and hasattr(endpoint, "delete")
    )


def test_mulitmethodroutes_with_prefix():
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

    app = Index(routes="/api" // routes)

    endpoint = app.router.search("http", "/api/user")[1]
    assert issubclass(endpoint, routes.base_class)
    assert hasattr(endpoint, "__methods__")
    assert (
        hasattr(endpoint, "get")
        and hasattr(endpoint, "post")
        and hasattr(endpoint, "delete")
    )


@pytest.mark.asyncio
async def test_mulitmethodroutes_with_parameters():
    from indexpy import Index, Path

    routes = Routes()

    @routes.http.get("/{name}", name=None)
    @routes.http.post("/{name}", name=None)
    @routes.http.put("/{name}", name=None)
    @routes.http.patch("/{name}", name=None)
    @routes.http.delete("/{name}", name=None)
    async def name(name: str = Path(...)):
        return name

    app = Index(routes=routes)

    async with TestClient(app) as client:
        resp = await client.get("/aber")
        assert resp.text == "aber"

        resp = await client.get("/")
        assert resp.status_code == 404
