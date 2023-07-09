import pytest

from pydantic import BaseModel
from kui.asgi import Kui
from async_asgi_testclient import TestClient


@pytest.mark.asyncio
async def test_pydantic_base_model():
    class Message(BaseModel):
        message: str

    app = Kui()

    @app.router.http("/message")
    async def message():
        return Message(message="Hello, World!")

    client = TestClient(app)
    response = await client.get("/message")
    assert response.status_code == 200
    assert response.json() == {"message": "Hello, World!"}
