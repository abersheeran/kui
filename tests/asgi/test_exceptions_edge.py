import httpx
import pytest

from kui.asgi import Kui, PlainTextResponse


@pytest.mark.asyncio
async def test_exception_handler_returning_none_raises_helpful_type_error():
    app = Kui()

    @app.exception_handler(ValueError)
    async def handle_value_error(exc: ValueError):
        return None

    @app.router.http.get("/")
    async def boom():
        raise ValueError("boom")

    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=app), base_url="http://testserver"
    ) as client:
        with pytest.raises(TypeError, match="Maybe you need to add a return statement"):
            await client.get("/")


@pytest.mark.asyncio
async def test_exception_handler_returning_unregistered_type_raises_type_error():
    app = Kui()

    @app.exception_handler(ValueError)
    async def handle_value_error(exc: ValueError):
        return object()

    @app.router.http.get("/")
    async def boom():
        raise ValueError("boom")

    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=app), base_url="http://testserver"
    ) as client:
        with pytest.raises(
            TypeError,
            match=r"Cannot find response_converter handler for this type: <class 'object'>",
        ):
            await client.get("/")


@pytest.mark.asyncio
async def test_custom_exception_handler_registered_via_decorator():
    app = Kui()

    @app.exception_handler(ValueError)
    async def handle_value_error(exc: ValueError):
        return PlainTextResponse(f"handled: {exc}", status_code=418)

    @app.router.http.get("/")
    async def boom():
        raise ValueError("boom")

    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=app), base_url="http://testserver"
    ) as client:
        response = await client.get("/")

    assert response.status_code == 418
    assert response.text == "handled: boom"


@pytest.mark.asyncio
async def test_no_match_found_returns_404():
    app = Kui()

    @app.router.http.get("/exists")
    async def exists():
        return "ok"

    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=app), base_url="http://testserver"
    ) as client:
        response = await client.get("/missing")

    assert response.status_code == 404
