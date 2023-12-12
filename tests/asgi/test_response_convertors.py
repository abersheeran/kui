from pathlib import Path

import pytest
from async_asgi_testclient import TestClient
from baize.asgi import Files, Response
from pydantic import BaseModel

from kui.asgi import Kui


@pytest.mark.asyncio
async def test_pydantic_base_model():
    class Message(BaseModel):
        message: str

    app = Kui()

    @app.router.http("/message")
    async def message():
        return Message(message="Hello, World!")

    @app.router.http("/{_:any}")
    async def static_files():
        return Files(Path(__file__).absolute().parent, handle_404=Response(404))

    client = TestClient(app)
    response = await client.get("/message")
    assert response.status_code == 200
    assert response.json() == {"message": "Hello, World!"}

    response = await client.get("/test_response_convertors.py")
    assert response.status_code == 200
