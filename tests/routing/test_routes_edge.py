from pathlib import PurePath

import pytest
from baize.datastructures import URL
from pydantic import BaseModel

from kui.asgi import FileResponse, JSONResponse, Kui, RedirectResponse
from kui.routing import NoRouteFound


def test_url_for_nonexistent_route_name_raises_no_route_found():
    app = Kui()

    with pytest.raises(NoRouteFound, match="No route with name 'missing' exists"):
        app.router.url_for("missing")


def test_response_converter_for_pure_path_returns_file_response():
    app = Kui()

    assert isinstance(app.response_converter(PurePath("README.md")), FileResponse)


def test_response_converter_for_base_model_returns_json_response():
    class Message(BaseModel):
        message: str

    app = Kui()

    assert isinstance(app.response_converter(Message(message="hello")), JSONResponse)


def test_response_converter_for_url_returns_redirect_response():
    app = Kui()

    assert isinstance(
        app.response_converter(URL("https://example.com")), RedirectResponse
    )
