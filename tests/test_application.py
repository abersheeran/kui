from pathlib import Path

import pytest
from async_asgi_testclient import TestClient


@pytest.mark.asyncio
async def test_example_application():
    from example import app

    async with TestClient(app) as client:
        response = await client.get("/")
        assert response.status_code == 200
        assert response.text == "hello, index.py"

        response = await client.get("/message")
        assert response.status_code == 200
        assert (
            response.text.replace(": ping\n\n", "")
            == "\n".join(f"id: {i}\ndata: hello\n" for i in range(5)) + "\n"
        )

        with pytest.raises(Exception, match="For get debug page."):
            response = await client.get("/exc")

        response = await client.get("/sources/README.md")
        assert response.status_code == 200
        assert response.content == (Path(".").absolute() / "README.md").read_bytes()

        response = await client.get("/sources/example")
        assert response.status_code == 404
