from __future__ import annotations


def test_decorator():
    from kui.asgi import Kui

    app = Kui()

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


def test_decorator_required_method():
    from kui.asgi import Kui

    app = Kui()

    @app.router.http.get("/get")
    async def need_get():
        ...

    @app.router.http.post("/post")
    async def need_post():
        ...

    @app.router.http.put("/put")
    async def need_put():
        ...

    @app.router.http.patch("/patch")
    async def need_patch():
        ...

    @app.router.http.delete("/delete")
    async def need_delete():
        ...

    assert app.router.search("http", "/get")[1].__name__ == "need_get"
    assert app.router.search("http", "/post")[1].__name__ == "need_post"
    assert app.router.search("http", "/put")[1].__name__ == "need_put"
    assert app.router.search("http", "/patch")[1].__name__ == "need_patch"
    assert app.router.search("http", "/delete")[1].__name__ == "need_delete"


def test_lshift():
    from kui.asgi import HttpRoute, Kui, SocketRoute

    app = Kui()

    async def hello():
        return "hello world"

    async def hello_ws():
        ...

    app.router = (
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
    from kui.asgi import Kui

    app = Kui()

    @app.router.http("/hello", name="hello")
    @app.router.http("/hello/{name}", name="hello-with-name")
    async def hello(request):
        return f"hello {request.path_params.get('name')}"

    assert app.router.url_for("hello") == "/hello"
    assert app.router.url_for("hello-with-name", {"name": "Aber"}) == "/hello/Aber"


def test_prefix():
    from kui.asgi import HttpRoute, Routes

    async def endpoint():
        pass

    assert [
        route.path
        for route in (
            "/auth"
            // Routes(
                HttpRoute("/login", endpoint),
                HttpRoute("/register", endpoint),
            )
        )
    ] == [
        route.path
        for route in (
            Routes(
                HttpRoute("/auth/login", endpoint),
                HttpRoute("/auth/register", endpoint),
            )
        )
    ]


def test_routes_operator():
    from kui.asgi import HttpRoute, Routes

    async def endpoint():
        pass

    routes = Routes()
    routes = routes << Routes(
        HttpRoute("/login", endpoint),
        HttpRoute("/register", endpoint),
    )
    assert routes == Routes(
        HttpRoute("/login", endpoint),
        HttpRoute("/register", endpoint),
    )

    assert (
        routes
        << Routes(
            HttpRoute("/login", endpoint),
            HttpRoute("/register", endpoint),
        )
    ) == (
        Routes(
            HttpRoute("/login", endpoint),
            HttpRoute("/register", endpoint),
        )
        + Routes(
            HttpRoute("/login", endpoint),
            HttpRoute("/register", endpoint),
        )
    )


def test_empty_path():
    from kui.asgi import Kui

    app = Kui()

    @app.router.http("")
    async def homepage():
        return "homepage"

    assert app.router.search("http", "/")[0] == {}
