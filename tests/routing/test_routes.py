def test_decorator():
    from indexpy import Index

    app = Index()

    @app.router.http("/hello", name="hello")
    async def hello():
        ...

    @app.router.websocket("/hello", name="hello_ws")
    async def hello_ws():
        ...

    assert app.router.search("http", "/hello")[0] == {}
    assert app.router.search("websocket", "/hello")[0] == {}

    assert app.router.search("http", "/hello") != (
        app.router.search("websocket", "/hello")
    )


def test_url_for():
    from indexpy import Index

    app = Index()

    @app.router.http("/hello", name="hello")
    @app.router.http("/hello/{name}", name="hello-with-name")
    async def hello(request):
        return f"hello {request.path_params.get('name')}"

    assert app.router.url_for("hello") == "/hello"
    assert app.router.url_for("hello-with-name", {"name": "Aber"}) == "/hello/Aber"


def test_prefix():
    from indexpy.routing import HttpRoute, Routes

    assert [
        route.path
        for route in (
            "/auth"
            // Routes(
                HttpRoute("/login", test_prefix),
                HttpRoute("/register", test_prefix),
            )
        )
    ] == [
        route.path
        for route in (
            Routes(
                HttpRoute("/auth/login", test_prefix),
                HttpRoute("/auth/register", test_prefix),
            )
        )
    ]
