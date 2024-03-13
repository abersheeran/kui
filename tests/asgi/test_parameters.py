import inspect
import io

import httpx
import pytest
from async_asgi_testclient import TestClient
from pydantic import BaseModel
from typing_extensions import Annotated

from kui.asgi import (
    Body,
    Cookie,
    Depends,
    Header,
    Kui,
    Path,
    Query,
    UploadFile,
)


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

    @app.router.http.post("/exclusive")
    async def exclusive(name: Annotated[str, Body(exclusive=True)]):
        return name

    async with TestClient(app) as client:
        resp = await client.post("/exclusive", json="aber")
        assert resp.text == "aber"


@pytest.mark.asyncio
async def test_depend():
    app = Kui()

    def get_name(name: Annotated[str, Body(...)]):
        return name

    @app.router.http.post("/")
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

    @app.router.http.post("/gen")
    async def depend_gen(name: Annotated[str, Depends(gen)]):
        assert in_gen
        return name

    async def async_get_name(name: Annotated[str, Body(...)]):
        return name

    @app.router.http.post("/async/")
    async def depend_async(name: Annotated[str, Depends(async_get_name)]):
        return name

    async def async_gen(name: Annotated[str, Query(...)]):
        nonlocal in_gen
        in_gen = True
        try:
            yield name
        finally:
            in_gen = False

    @app.router.http.post("/async/gen")
    async def depend_async_gen(name: Annotated[str, Depends(async_gen)]):
        assert in_gen
        return name

    count = 0

    async def cached_get_name(name: Annotated[str, Body(...)]):
        nonlocal count
        count += 1
        return name

    @app.router.http.post("/cache/enable")
    async def cache_enable(
        name0: Annotated[str, Depends(cached_get_name, cache=True)],
        name1: Annotated[str, Depends(cached_get_name, cache=True)],
    ):
        assert name0 == name1
        return name0

    @app.router.http.post("/cache/disable")
    async def cache_disable(
        name0: Annotated[str, Depends(cached_get_name, cache=False)],
        name1: Annotated[str, Depends(cached_get_name, cache=False)],
    ):
        assert name0 == name1
        return name0

    async with TestClient(app) as client:
        resp = await client.post("/", json={"name": "aber"})
        assert resp.text == "aber"

        resp = await client.post("/gen", query_string={"name": "123"})
        assert resp.text == "123"
        assert not in_gen

        resp = await client.post("/async/", json={"name": "123"})
        assert resp.text == "123"

        resp = await client.post("/async/gen", query_string={"name": "123"})
        assert resp.text == "123"
        assert not in_gen

        resp = await client.post("/cache/enable", json={"name": "123"})
        assert resp.text == "123"
        assert count == 1

        resp = await client.post("/cache/disable", json={"name": "123"})
        assert resp.text == "123"
        assert count == 3


@pytest.mark.asyncio
async def test_middleware():
    app = Kui()

    def middleware(endpoint):
        async def middleware_wrapper(query: Annotated[str, Query(...)]):
            return await endpoint()

        return middleware_wrapper

    @app.router.http.get("/", middlewares=[middleware])
    async def cookie(name: Annotated[str, Cookie()]):
        return name

    async with TestClient(app) as client:
        resp = await client.get("/", cookies={"name": "aber"})
        assert resp.status_code == 422

        resp = await client.get("/?query=123", cookies={"name": "aber"})
        assert resp.text == "aber"

    assert not inspect.signature(app.router.search("http", "/")[1]).parameters


@pytest.mark.asyncio
async def test_upload_file():
    app = Kui()

    @app.router.http.post("/")
    async def upload_file(file: Annotated[UploadFile, Body(...)]):
        return {
            "filename": file.filename,
            "content": file.read().decode("utf8"),
        }

    async with httpx.AsyncClient(app=app, base_url="http://testserver") as client:
        resp = await client.post("/", files={"file": ("file", io.BytesIO(b"123"))})
        assert resp.json() == {"filename": "file", "content": "123"}

        resp = await client.post("/", files={"file0": io.BytesIO(b"123")})
        assert resp.status_code == 422


@pytest.mark.asyncio
async def test_parameters_nest_model():
    app = Kui()

    class User(BaseModel):
        name: str
        age: int

    @app.router.http.post("/")
    async def create_user(user: Annotated[User, Body(...)]):
        assert user.age >= 18
        return user

    async with httpx.AsyncClient(app=app, base_url="http://testserver") as client:
        resp = await client.post("/", json={"user": {"name": "aber", "age": 18}})
        assert resp.json() == {"name": "aber", "age": 18}

        resp = await client.post("/", json={"name": "aber", "age": 18})
        assert resp.status_code == 422
