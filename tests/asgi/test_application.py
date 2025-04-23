from __future__ import annotations

from pathlib import Path

import httpx
import pytest


def test_application():
    from kui.asgi import Kui
    from kui.utils import State

    app = Kui()
    with pytest.raises(RuntimeError):
        app.state = State()

    with pytest.raises(RuntimeError):
        del app.state


@pytest.mark.asyncio
async def test_example_application():
    from example import app

    app.state.wait_time = 0.00000001

    async with httpx.AsyncClient(
        base_url="http://testserver", transport=httpx.ASGITransport(app=app)
    ) as client:
        response = await client.get("/")
        assert response.status_code == 200
        assert response.text == "Kuí"

        response = await client.get("/message")
        assert response.status_code == 200
        assert (
            response.text.replace(": ping\n\n", "")
            == "\n".join(f"id: {i}\ndata: hello\n" for i in range(5)) + "\n"
        )

        response = await client.get("/sources/README.md")
        assert response.status_code == 200
        assert response.content == (Path(".").absolute() / "README.md").read_bytes()

        response = await client.get("/sources/example")
        assert response.status_code == 404


def test_custom_application_response_converter():
    from dataclasses import asdict, dataclass
    from typing import Mapping

    from kui.asgi import HttpResponse, JSONResponse, Kui, PlainTextResponse

    @dataclass
    class Error:
        code: int = 0
        title: str = ""
        message: str = ""

    app = Kui(
        response_converters={
            Error: lambda error, status=400, headers=None: JSONResponse(
                asdict(error), status, headers
            ),
        }
    )

    @app.response_converter.register(tuple)
    @app.response_converter.register(list)
    @app.response_converter.register(dict)
    def _more_json(
        body, status: int = 200, headers: Mapping[str, str] | None = None
    ) -> HttpResponse:
        return PlainTextResponse(str(body), status, headers)

    assert isinstance(app.response_converter(Error()), JSONResponse)
    assert isinstance(app.response_converter(tuple()), PlainTextResponse)
    assert isinstance(app.response_converter(list()), PlainTextResponse)
    assert isinstance(app.response_converter(dict()), PlainTextResponse)
