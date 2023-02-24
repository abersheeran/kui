import httpx
import pytest

from kui.asgi import HttpView, Kui


@pytest.mark.asyncio
async def test_http_view():
    app = Kui()

    @app.router.http("/")
    class Home(HttpView):
        @staticmethod
        async def get():
            return "OK"

    async with httpx.AsyncClient(app=app, base_url="http://testServer") as client:
        assert (await client.get("/")).content == b"OK"

        assert (await client.post("/")).status_code == 405
