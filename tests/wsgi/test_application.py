from pathlib import Path

import pytest
from httpx import Client


def test_application():
    from hintapi import HintAPI

    app = HintAPI()
    with pytest.raises(RuntimeError):
        app.debug = True

    with pytest.raises(RuntimeError):
        del app.debug


def test_example_application():
    from example import app

    app.state.wait_time = 0.00000001

    with Client(app=app, base_url="http://localhost") as client:
        response = client.get("/")
        assert response.status_code == 200
        assert response.text == "hello, hintapi"

        response = client.get("/message")
        assert response.status_code == 200
        assert (
            response.text.replace(": ping\n\n", "")
            == "\n".join(f"id: {i}\ndata: hello\n" for i in range(5)) + "\n"
        )

        with pytest.raises(Exception, match="For get debug page."):
            response = client.get("/exc")

        with pytest.raises(Exception, match="For get debug page."):
            response = client.get("/exc", headers={"accept": "text/plain;"})

        response = client.get("/sources/README.md")
        assert response.status_code == 200
        assert response.content == (Path(".").absolute() / "README.md").read_bytes()

        response = client.get("/sources/example")
        assert response.status_code == 404


def test_custom_application_response_converter():
    from dataclasses import asdict, dataclass
    from typing import Mapping

    from hintapi import HintAPI, HttpResponse, JSONResponse, PlainTextResponse

    @dataclass
    class Error:
        code: int = 0
        title: str = ""
        message: str = ""

    app = HintAPI(
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
        body, status: int = 200, headers: Mapping[str, str] = None
    ) -> HttpResponse:
        return PlainTextResponse(str(body), status, headers)

    assert isinstance(app.response_converter(Error()), JSONResponse)
    assert isinstance(app.response_converter(tuple()), PlainTextResponse)
    assert isinstance(app.response_converter(list()), PlainTextResponse)
    assert isinstance(app.response_converter(dict()), PlainTextResponse)
