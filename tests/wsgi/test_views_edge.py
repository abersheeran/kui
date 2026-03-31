import httpx
import pytest

from kui.wsgi import HttpRoute, HttpView, Kui, required_method


def test_wsgi_required_method_rejects_non_function():
    with pytest.raises(TypeError, match="can only decorate function"):

        @required_method("GET")
        class NotAFunction:
            pass


def test_wsgi_required_method_options():
    app = Kui()

    def handler():
        return "ok"

    app.router <<= HttpRoute("/x", handler) @ required_method("GET")

    with httpx.Client(
        transport=httpx.WSGITransport(app=app), base_url="http://testserver"
    ) as client:
        response = client.options("/x")

    assert response.status_code == 200
    assert "GET" in response.headers["allow"]


def test_wsgi_required_method_405():
    app = Kui()

    def handler():
        return "ok"

    app.router <<= HttpRoute("/x", handler) @ required_method("GET")

    with httpx.Client(
        transport=httpx.WSGITransport(app=app), base_url="http://testserver"
    ) as client:
        response = client.post("/x")

    assert response.status_code == 405
    assert "GET" in response.headers["allow"]
