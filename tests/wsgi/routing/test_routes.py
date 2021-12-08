def test_decorator():
    from hintapi import HintAPI

    app = HintAPI()

    @app.router.http("/hello", name="hello")
    def hello():
        ...

    @app.router.websocket("/hello", name="hello_ws")
    def hello_ws():
        ...

    assert app.router.search("http", "/hello")[0] == {}
    assert app.router.search("websocket", "/hello")[0] == {}

    assert app.router.search("http", "/hello") != (
        app.router.search("websocket", "/hello")
    )


def test_decorator_required_method():
    from hintapi import HintAPI

    app = HintAPI()

    @app.router.http.get("/get")
    def need_get():
        ...

    @app.router.http.post("/post")
    def need_post():
        ...

    @app.router.http.put("/put")
    def need_put():
        ...

    @app.router.http.patch("/patch")
    def need_patch():
        ...

    @app.router.http.delete("/delete")
    def need_delete():
        ...

    assert app.router.search("http", "/get")[1].__name__ == "need_get"
    assert app.router.search("http", "/post")[1].__name__ == "need_post"
    assert app.router.search("http", "/put")[1].__name__ == "need_put"
    assert app.router.search("http", "/patch")[1].__name__ == "need_patch"
    assert app.router.search("http", "/delete")[1].__name__ == "need_delete"


def test_lshift():
    from hintapi import HintAPI
    from hintapi.routing import HttpRoute, SocketRoute

    app = HintAPI()

    def hello():
        return "hello world"

    def hello_ws():
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
    from hintapi import HintAPI

    app = HintAPI()

    @app.router.http("/hello", name="hello")
    @app.router.http("/hello/{name}", name="hello-with-name")
    def hello(request):
        return f"hello {request.path_params.get('name')}"

    assert app.router.url_for("hello") == "/hello"
    assert app.router.url_for("hello-with-name", {"name": "Aber"}) == "/hello/Aber"


def test_prefix():
    from hintapi.routing import HttpRoute, Routes

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
    from hintapi import HttpRoute, Routes

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


def test_empty_path():
    from hintapi import HintAPI

    app = HintAPI()

    @app.router.http("")
    def homepage():
        return "homepage"

    assert app.router.search("http", "/")[0] == {}
