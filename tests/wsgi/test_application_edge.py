import httpx

from kui.wsgi import HTTPException, Kui


def test_wsgi_404_for_unmapped_route():
    app = Kui()

    with httpx.Client(
        transport=httpx.WSGITransport(app=app), base_url="http://testserver"
    ) as client:
        response = client.get("/nonexistent")

    assert response.status_code == 404


def test_wsgi_tuple_response_with_status():
    app = Kui()

    @app.router.http.post("/")
    def create():
        return {"created": True}, 201

    with httpx.Client(
        transport=httpx.WSGITransport(app=app), base_url="http://testserver"
    ) as client:
        response = client.post("/")

    assert response.status_code == 201
    assert response.json() == {"created": True}


def test_wsgi_tuple_response_with_headers():
    app = Kui()

    @app.router.http.get("/")
    def homepage():
        return {"ok": True}, 200, {"X-Custom": "val"}

    with httpx.Client(
        transport=httpx.WSGITransport(app=app), base_url="http://testserver"
    ) as client:
        response = client.get("/")

    assert response.status_code == 200
    assert response.json() == {"ok": True}
    assert response.headers["x-custom"] == "val"


def test_wsgi_exception_handler_decorator():
    app = Kui()

    @app.exception_handler(ValueError)
    def handle_value_error(exc: ValueError):
        return {"error": str(exc)}, 400

    @app.router.http.get("/")
    def homepage():
        raise ValueError("bad input")

    with httpx.Client(
        transport=httpx.WSGITransport(app=app), base_url="http://testserver"
    ) as client:
        response = client.get("/")

    assert response.status_code == 400
    assert response.json() == {"error": "bad input"}


def test_wsgi_http_exception_204():
    app = Kui()

    @app.router.http.get("/")
    def homepage():
        raise HTTPException(204)

    with httpx.Client(
        transport=httpx.WSGITransport(app=app), base_url="http://testserver"
    ) as client:
        response = client.get("/")

    assert response.status_code == 204
    assert response.content == b""
