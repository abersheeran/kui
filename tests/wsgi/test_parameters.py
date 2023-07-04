import inspect
import io

import httpx
from httpx import Client
from typing_extensions import Annotated

from kui.wsgi import (
    Body,
    Cookie,
    Depends,
    Header,
    Kui,
    Path,
    Query,
    UploadFile,
)


def test_path():
    app = Kui()

    @app.router.http.get("/")
    @app.router.http.get("/{name}", name=None)
    @app.router.http.get("/{id:int}", name=None)
    def path(name: Annotated[str, Path()]):
        return name

    with Client(app=app, base_url="http://testServer") as client:
        resp = client.get("/aber")
        assert resp.text == "aber"

        resp = client.get("/")
        assert resp.status_code == 404

        resp = client.get("/1")
        assert resp.status_code == 404

    assert not inspect.signature(app.router.search("http", "/aber")[1]).parameters


def test_query():
    app = Kui()

    @app.router.http.get("/")
    def query(name: Annotated[str, Query(...)]):
        return name

    with Client(app=app, base_url="http://testServer") as client:
        resp = client.get("/", params={"name": "aber"})
        assert resp.text == "aber"

        resp = client.get("/", params={})
        assert resp.status_code == 422

    assert not inspect.signature(app.router.search("http", "/")[1]).parameters


def test_header():
    app = Kui()

    @app.router.http.get("/")
    def header(name: Annotated[str, Header(alias="Name")]):
        return name

    with Client(app=app, base_url="http://testServer") as client:
        resp = client.get("/", headers={"name": "aber"})
        assert resp.text == "aber"

        resp = client.get("/", headers={"name0": "aber"})
        assert resp.status_code == 422

    assert not inspect.signature(app.router.search("http", "/")[1]).parameters


def test_cookie():
    app = Kui()

    @app.router.http.get("/")
    def cookie(name: Annotated[str, Cookie()]):
        return name

    with Client(
        app=app, base_url="http://testServer", cookies={"name": "aber"}
    ) as client:
        resp = client.get("/")
        assert resp.text == "aber"

    with Client(
        app=app, base_url="http://testServer", cookies={"name0": "aber"}
    ) as client:
        resp = client.get("/")
        assert resp.status_code == 422

    assert not inspect.signature(app.router.search("http", "/")[1]).parameters


def test_body():
    app = Kui()

    @app.router.http.post("/")
    def body(name: Annotated[str, Body()]):
        return name

    with Client(app=app, base_url="http://testServer") as client:
        resp = client.post("/", data={"name": "aber"})
        assert resp.text == "aber"

        resp = client.post("/", data={"name0": "aber"})
        assert resp.status_code == 422

    assert not inspect.signature(app.router.search("http", "/")[1]).parameters


def test_depend():
    app = Kui()

    def get_name(name: Annotated[str, Body(...)]):
        return name

    @app.router.http.post("/")
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

    @app.router.http.post("/gen")
    def depend_gen(name: Annotated[str, Depends(gen)]):
        assert in_gen
        return name

    def async_get_name(name: Annotated[str, Body(...)]):
        return name

    @app.router.http.post("/async/")
    def depend_async(name: Annotated[str, Depends(async_get_name)]):
        return name

    def async_gen(name: Annotated[str, Query(...)]):
        nonlocal in_gen
        in_gen = True
        try:
            yield name
        finally:
            in_gen = False

    @app.router.http.post("/async/gen")
    def depend_async_gen(name: Annotated[str, Depends(async_gen)]):
        assert in_gen
        return name

    with Client(app=app, base_url="http://testServer") as client:
        resp = client.post("/", json={"name": "aber"})
        assert resp.text == "aber"

        resp = client.post("/gen", params={"name": "123"})
        assert resp.text == "123"
        assert not in_gen

        resp = client.post("/async/", json={"name": "123"})
        assert resp.text == "123"

        resp = client.post("/async/gen", params={"name": "123"})
        assert resp.text == "123"
        assert not in_gen


def test_middleware():
    app = Kui()

    def middleware(endpoint):
        def middleware_wrapper(query: Annotated[str, Query(...)]):
            return endpoint()

        return middleware_wrapper

    @app.router.http.get("/", middlewares=[middleware])
    def cookie(name: Annotated[str, Cookie()]):
        return name

    with Client(
        app=app, base_url="http://testServer", cookies={"name": "aber"}
    ) as client:
        resp = client.get("/")
        assert resp.status_code == 422

        resp = client.get("/?query=123")
        assert resp.text == "aber"

    assert not inspect.signature(app.router.search("http", "/")[1]).parameters


def test_upload_file():
    app = Kui()

    @app.router.http.post("/")
    def upload_file(file: Annotated[UploadFile, Body(...)]):
        return {
            "filename": file.filename,
            "content": file.read().decode("utf8"),
        }

    with httpx.Client(app=app, base_url="http://testserver") as client:
        resp = client.post("/", files={"file": ("file", io.BytesIO(b"123"))})
        assert resp.json() == {"filename": "file", "content": "123"}

        resp = client.post("/", files={"file0": io.BytesIO(b"123")})
        assert resp.status_code == 422
