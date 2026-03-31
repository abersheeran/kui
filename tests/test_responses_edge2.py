from datetime import datetime

import httpx
import pytest

from kui.asgi import Kui


@pytest.mark.asyncio
async def test_custom_json_encoder_overrides_default_jsonable_conversion():
    app = Kui(json_encoder={datetime: lambda dt: f"custom:{dt.isoformat()}"})

    @app.router.http.get("/")
    async def handler():
        return {"time": datetime(2024, 1, 1, 12, 0, 0)}

    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=app), base_url="http://testserver"
    ) as client:
        response = await client.get("/")

    assert response.status_code == 200
    assert response.json()["time"] == "custom:2024-01-01T12:00:00"
