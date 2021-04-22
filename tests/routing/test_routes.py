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


def test_lshift():
    from indexpy import Index
    from indexpy.routing import HttpRoute, SocketRoute

    app = Index()

    async def hello():
        return "hello world"

    async def hello_ws():
        ...

    (
        app.router
        << HttpRoute("/hello", hello, name="hello")
        << SocketRoute("/hello", hello_ws, name="hello_ws")
    )

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


def test_routes_operator():
    from indexpy import HttpRoute, Routes

    routes = Routes()
    routes << Routes(
        HttpRoute("/login", test_routes_operator),
        HttpRoute("/register", test_routes_operator),
    )
    routes == Routes(
        HttpRoute("/login", test_routes_operator),
        HttpRoute("/register", test_routes_operator),
    )

    (
        routes
        << Routes(
            HttpRoute("/login", test_routes_operator),
            HttpRoute("/register", test_routes_operator),
        )
    ) == (
        Routes(
            HttpRoute("/login", test_routes_operator),
            HttpRoute("/register", test_routes_operator),
        )
        + Routes(
            HttpRoute("/login", test_routes_operator),
            HttpRoute("/register", test_routes_operator),
        )
    )
