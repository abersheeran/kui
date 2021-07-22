from pathlib import Path

import pytest
from async_asgi_testclient import TestClient


@pytest.mark.asyncio
async def test_example_application():
    from example import app

    app.state.wait_time = 0.00000001

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

        with pytest.raises(Exception, match="For get debug page."):
            response = await client.get("/exc", headers={"accept": "text/plain;"})

        response = await client.get("/sources/README.md")
        assert response.status_code == 200
        assert response.content == (Path(".").absolute() / "README.md").read_bytes()

        response = await client.get("/sources/example")
        assert response.status_code == 404

        async with client.websocket_connect("/") as socket:
            assert await socket.receive_json() == {"data": "(^_^)"}


def test_custom_application_response_convertor():
    from dataclasses import asdict, dataclass
    from typing import Mapping

    from indexpy import HttpResponse, Index, JSONResponse, PlainTextResponse

    app = Index()

    @dataclass
    class Error:
        code: int = 0
        title: str = ""
        message: str = ""

    @app.response_convertor.register(Error)
    def _error_json(
        error: Error, status: int = 400, headers: Mapping[str, str] = None
    ) -> HttpResponse:
        return JSONResponse(asdict(error), status, headers)

    @app.response_convertor.register(tuple)
    @app.response_convertor.register(list)
    @app.response_convertor.register(dict)
    def _more_json(
        body, status: int = 200, headers: Mapping[str, str] = None
    ) -> HttpResponse:
        return PlainTextResponse(str(body), status, headers)

    assert isinstance(app.response_convertor(Error()), JSONResponse)
    assert isinstance(app.response_convertor(tuple()), PlainTextResponse)
    assert isinstance(app.response_convertor(list()), PlainTextResponse)
    assert isinstance(app.response_convertor(dict()), PlainTextResponse)
