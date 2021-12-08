import inspect

import pytest
from httpx import Client
from typing_extensions import Annotated

from hintapi import Body, Cookie, Depends, Header, Path, Query, Request
from hintapi.applications import HintAPI


def test_path():
    app = HintAPI()

    @app.router.http.get("/")
    @app.router.http.get("/{name}", name=None)
    @app.router.http.get("/{id:int}", name=None)
    def path(name: Annotated[str, Path()]):
        return name

    with Client(app=app, base_url="http://localhost") as client:
        resp = client.get("/aber")
        assert resp.text == "aber"

        resp = client.get("/")
        assert resp.status_code == 404

        resp = client.get("/1")
        assert resp.status_code == 404

    assert not inspect.signature(app.router.search("http", "/aber")[1]).parameters


def test_query():
    app = HintAPI()

    @app.router.http.get("/")
    def query(name: Annotated[str, Query(...)]):
        return name

    with Client(app=app, base_url="http://localhost") as client:
        resp = client.get("/", params={"name": "aber"})
        assert resp.text == "aber"

        resp = client.get("/", params={})
        assert resp.status_code == 422

    assert not inspect.signature(app.router.search("http", "/")[1]).parameters


def test_header():
    app = HintAPI()

    @app.router.http.get("/")
    def header(name: Annotated[str, Header()]):
        return name

    with Client(app=app, base_url="http://localhost") as client:
        resp = client.get("/", headers={"name": "aber"})
        assert resp.text == "aber"

        resp = client.get("/", headers={"name0": "aber"})
        assert resp.status_code == 422

    assert not inspect.signature(app.router.search("http", "/")[1]).parameters


def test_cookie():
    app = HintAPI()

    @app.router.http.get("/")
    def cookie(name: Annotated[str, Cookie()]):
        return name

    with Client(
        app=app, base_url="http://localhost", cookies={"name": "aber"}
    ) as client:
        resp = client.get("/")
        assert resp.text == "aber"

    with Client(
        app=app, base_url="http://localhost", cookies={"name0": "aber"}
    ) as client:
        resp = client.get("/")
        assert resp.status_code == 422

    assert not inspect.signature(app.router.search("http", "/")[1]).parameters


def test_body():
    app = HintAPI()

    @app.router.http.post("/")
    def body(name: Annotated[str, Body()]):
        return name

    with Client(app=app, base_url="http://localhost") as client:
        resp = client.post("/", data={"name": "aber"})
        assert resp.text == "aber"

        resp = client.post("/", data={"name0": "aber"})
        assert resp.status_code == 422

    assert not inspect.signature(app.router.search("http", "/")[1]).parameters


def test_request():
    app0 = HintAPI()

    @app0.router.http.get("/")
    def homepage(app: Annotated[HintAPI, Request()]):
        return str(app is app0)

    @app0.router.http.get("/no-attr")
    def no_attr(application: Annotated[HintAPI, Request()]):
        return str(application is app0)

    @app0.router.http.get("/no-attr-with-default")
    def no_attr_with_default(application: Annotated[HintAPI, Request(app0)]):
        return str(application is app0)

    @app0.router.http.get("/no-attr-with-default-factory")
    def no_attr_with_default_factory(
        application: Annotated[HintAPI, Request(default_factory=lambda: app0)],
    ):
        return str(application is app0)

    with Client(app=app0, base_url="http://localhost") as client:
        resp = client.get("/")
        assert resp.text == "True"

        with pytest.raises(AttributeError):
            client.get("/no-attr")

        resp = client.get("/no-attr-with-default")
        assert resp.text == "True"

        resp = client.get("/no-attr-with-default-factory")
        assert resp.text == "True"

    assert not inspect.signature(app0.router.search("http", "/")[1]).parameters


def test_depend():
    app = HintAPI()

    def get_name(name: Annotated[str, Body(...)]):
        return name

    @app.router.http("/")
    def homepage(name: Annotated[str, Depends(get_name)]):
        return name

    in_gen = False

    def gen(name: Annotated[str, Query(...)]):
        nonlocal in_gen
        in_gen = True
        try:
            yield name
        finally:
            in_gen = False

    @app.router.http.get("/gen")
    def depend_gen(name: Annotated[str, Depends(gen)]):
        assert in_gen
        return name

    def async_get_name(name: Annotated[str, Body(...)]):
        return name

    with Client(app=app, base_url="http://localhost") as client:
        resp = client.post("/", json={"name": "aber"})
        assert resp.status_code == 200
        assert resp.text == "aber"

        resp = client.get("/gen", params={"name": "123"})
        assert resp.status_code == 200
        assert resp.text == "123"
        assert not in_gen


def test_middleware():
    app = HintAPI()

    def middleware(endpoint):
        def middleware_wrapper(query: str = Query(...)):
            return endpoint()

        return middleware_wrapper

    @app.router.http.get("/", middlewares=[middleware])
    def cookie(name: str = Cookie()):
        return name

    with Client(
        app=app, base_url="http://localhost", cookies={"name": "aber"}
    ) as client:
        resp = client.get("/")
        assert resp.status_code == 422

    with Client(
        app=app, base_url="http://localhost", cookies={"name": "aber"}
    ) as client:
        resp = client.get("/?query=123")
        assert resp.text == "aber"

    assert not inspect.signature(app.router.search("http", "/")[1]).parameters
