from pathlib import Path

import pytest

from baize.asgi import Files
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

    @app.router.http("/static/{_:any}")
    async def static_files():
        return Files(Path(__file__).absolute().parent)

    client = TestClient(app)
    response = await client.get("/message")
    assert response.status_code == 200
    assert response.json() == {"message": "Hello, World!"}

    response = await client.get("/static/test_response_convertors.py")
    assert response.status_code == 200
