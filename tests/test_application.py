import pytest
from async_asgi_testclient import TestClient


@pytest.mark.asyncio
async def test_application():
    from example import app

    async with TestClient(app) as client:
        response = await client.get("/")
        assert response.status_code == 200
        assert response.text == "hello, index.py"
