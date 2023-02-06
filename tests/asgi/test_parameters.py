import inspect

import pytest
from async_asgi_testclient import TestClient
from typing_extensions import Annotated

from kui.asgi import Body, Cookie, Depends, Header, Kui, Path, Query, RequestAttr


@pytest.mark.asyncio
async def test_path():
    app = Kui()

    @app.router.http.get("/")
    @app.router.http.get("/{name}", name=None)
    @app.router.http.get("/{id:int}", name=None)
    async def path(name: Annotated[str, Path()]):
        return name

    async with TestClient(app) as client:
        resp = await client.get("/aber")
        assert resp.text == "aber"

        resp = await client.get("/")
        assert resp.status_code == 404

        resp = await client.get("/1")
        assert resp.status_code == 404

    assert not inspect.signature(app.router.search("http", "/aber")[1]).parameters


@pytest.mark.asyncio
async def test_query():
    app = Kui()

    @app.router.http.get("/")
    async def query(name: Annotated[str, Query(...)]):
        return name

    async with TestClient(app) as client:
        resp = await client.get("/", query_string={"name": "aber"})
        assert resp.text == "aber"

        resp = await client.get("/", query_string={})
        assert resp.status_code == 422

    assert not inspect.signature(app.router.search("http", "/")[1]).parameters


@pytest.mark.asyncio
async def test_header():
    app = Kui()

    @app.router.http.get("/")
    async def header(name: Annotated[str, Header(alias="Name")]):
        return name

    async with TestClient(app) as client:
        resp = await client.get("/", headers={"name": "aber"})
        assert resp.text == "aber"

        resp = await client.get("/", headers={"name0": "aber"})
        assert resp.status_code == 422

    assert not inspect.signature(app.router.search("http", "/")[1]).parameters


@pytest.mark.asyncio
async def test_cookie():
    app = Kui()

    @app.router.http.get("/")
    async def cookie(name: Annotated[str, Cookie()]):
        return name

    async with TestClient(app) as client:
        resp = await client.get("/", cookies={"name": "aber"})
        assert resp.text == "aber"

        resp = await client.get("/", cookies={"name0": "aber"})
        assert resp.status_code == 422

    assert not inspect.signature(app.router.search("http", "/")[1]).parameters


@pytest.mark.asyncio
async def test_body():
    app = Kui()

    @app.router.http.post("/")
    async def body(name: Annotated[str, Body()]):
        return name

    async with TestClient(app) as client:
        resp = await client.post("/", form={"name": "aber"})
        assert resp.text == "aber"

        resp = await client.post("/", form={"name0": "aber"})
        assert resp.status_code == 422

    assert not inspect.signature(app.router.search("http", "/")[1]).parameters


@pytest.mark.asyncio
async def test_request():
    app0 = Kui()

    @app0.router.http.get("/")
    async def homepage(app: Annotated[Kui, RequestAttr()]):
        return str(app is app0)

    @app0.router.http.get("/no-attr")
    async def no_attr(application: Annotated[Kui, RequestAttr()]):
        return str(application is app0)

    @app0.router.http.get("/no-attr-with-default")
    async def no_attr_with_default(application: Annotated[Kui, RequestAttr(app0)]):
        return str(application is app0)

    @app0.router.http.get("/no-attr-with-default-factory")
    async def no_attr_with_default_factory(
        application: Annotated[Kui, RequestAttr(default_factory=lambda: app0)],
    ):
        return str(application is app0)

    async with TestClient(app0) as client:
        resp = await client.get("/")
        assert resp.text == "True"

        with pytest.raises(AttributeError):
            await client.get("/no-attr")

        resp = await client.get("/no-attr-with-default")
        assert resp.text == "True"

        resp = await client.get("/no-attr-with-default-factory")
        assert resp.text == "True"

    assert not inspect.signature(app0.router.search("http", "/")[1]).parameters


@pytest.mark.asyncio
async def test_depend():
    app = Kui()

    def get_name(name: Annotated[str, Body(...)]):
        return name

    @app.router.http.get("/")
    async def homepage(name: Annotated[str, Depends(get_name)]):
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
    async def depend_gen(name: Annotated[str, Depends(gen)]):
        assert in_gen
        return name

    async def async_get_name(name: Annotated[str, Body(...)]):
        return name

    @app.router.http.get("/async/")
    async def depend_async(name: Annotated[str, Depends(async_get_name)]):
        return name

    async def async_gen(name: Annotated[str, Query(...)]):
        nonlocal in_gen
        in_gen = True
        try:
            yield name
        finally:
            in_gen = False

    @app.router.http.get("/async/gen")
    async def depend_async_gen(name: Annotated[str, Depends(async_gen)]):
        assert in_gen
        return name

    async with TestClient(app) as client:
        resp = await client.get("/", json={"name": "aber"})
        assert resp.text == "aber"

        resp = await client.get("/gen", query_string={"name": "123"})
        assert resp.text == "123"
        assert not in_gen

        resp = await client.get("/async/", json={"name": "123"})
        assert resp.text == "123"

        resp = await client.get("/async/gen", query_string={"name": "123"})
        assert resp.text == "123"
        assert not in_gen


@pytest.mark.asyncio
async def test_middleware():
    app = Kui()

    def middleware(endpoint):
        async def middleware_wrapper(query: str = Query(...)):
            return await endpoint()

        return middleware_wrapper

    @app.router.http.get("/", middlewares=[middleware])
    async def cookie(name: str = Cookie()):
        return name

    async with TestClient(app) as client:
        resp = await client.get("/", cookies={"name": "aber"})
        assert resp.status_code == 422

        resp = await client.get("/?query=123", cookies={"name": "aber"})
        assert resp.text == "aber"

    assert not inspect.signature(app.router.search("http", "/")[1]).parameters
