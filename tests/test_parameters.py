import pytest
from async_asgi_testclient import TestClient

from indexpy import Body, Cookie, Header, Path, Query, Request
from indexpy.applications import Index


@pytest.mark.asyncio
async def test_path():
    app = Index()

    @app.router.http.get("/")
    @app.router.http.get("/{name}", name=None)
    @app.router.http.get("/{id:int}", name=None)
    async def path(name: str = Path()):
        return name

    async with TestClient(app) as client:
        resp = await client.get("/aber")
        assert resp.text == "aber"

        resp = await client.get("/")
        assert resp.status_code == 422

        resp = await client.get("/1")
        assert resp.status_code == 422


@pytest.mark.asyncio
async def test_query():
    app = Index()

    @app.router.http.get("/")
    async def query(name: str = Query(...)):
        return name

    async with TestClient(app) as client:
        resp = await client.get("/", query_string={"name": "aber"})
        assert resp.text == "aber"

        resp = await client.get("/", query_string={})
        assert resp.status_code == 422


@pytest.mark.asyncio
async def test_header():
    app = Index()

    @app.router.http.get("/")
    async def header(name: str = Header()):
        return name

    async with TestClient(app) as client:
        resp = await client.get("/", headers={"name": "aber"})
        assert resp.text == "aber"

        resp = await client.get("/", headers={"name0": "aber"})
        assert resp.status_code == 422


@pytest.mark.asyncio
async def test_cookie():
    app = Index()

    @app.router.http.get("/")
    async def cookie(name: str = Cookie()):
        return name

    async with TestClient(app) as client:
        resp = await client.get("/", cookies={"name": "aber"})
        assert resp.text == "aber"

        resp = await client.get("/", cookies={"name0": "aber"})
        assert resp.status_code == 422


@pytest.mark.asyncio
async def test_body():
    app = Index()

    @app.router.http.post("/")
    async def body(name: str = Body()):
        return name

    async with TestClient(app) as client:
        resp = await client.post("/", form={"name": "aber"})
        assert resp.text == "aber"

        resp = await client.post("/", form={"name0": "aber"})
        assert resp.status_code == 422


@pytest.mark.asyncio
async def test_request():
    app0 = Index()

    @app0.router.http.get("/")
    async def homepage(app: str = Request()):
        return str(app is app0)

    @app0.router.http.get("/no-attr")
    async def no_attr(application: str = Request()):
        return str(application is app0)

    async with TestClient(app0) as client:
        resp = await client.get("/")
        assert resp.text == "True"

        with pytest.raises(AttributeError):
            await client.get("/no-attr")
