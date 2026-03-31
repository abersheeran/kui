import httpx
import pytest
from typing_extensions import Annotated

from kui.asgi import Body, HTTPException, Kui


@pytest.mark.asyncio
async def test_unsupported_media_type():
    app = Kui()

    @app.router.http.post("/")
    async def handler(data: Annotated[dict, Body(exclusive=True)]):
        return data

    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=app), base_url="http://testserver"
    ) as client:
        response = await client.post(
            "/", content=b"raw", headers={"content-type": "application/xml"}
        )

    assert response.status_code == 415


@pytest.mark.asyncio
async def test_http_exception_204_no_body():
    app = Kui()

    @app.router.http.get("/")
    async def handler():
        raise HTTPException(204)

    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=app), base_url="http://testserver"
    ) as client:
        response = await client.get("/")

    assert response.status_code == 204
    assert response.content == b""


@pytest.mark.asyncio
async def test_handler_returning_none_raises_helpful_type_error():
    app = Kui()

    @app.router.http.get("/")
    async def handler():
        return None

    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=app), base_url="http://testserver"
    ) as client:
        with pytest.raises(TypeError, match="Maybe you need to add a return statement"):
            await client.get("/")
