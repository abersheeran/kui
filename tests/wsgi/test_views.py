import httpx

from kui.wsgi import HttpView, Kui


def test_http_view():
    app = Kui()

    @app.router.http("/")
    class Home(HttpView):
        @classmethod
        def get(cls):
            return "OK"

    with httpx.Client(
        base_url="http://testServer",
        transport=httpx.WSGITransport(app=app),  # type: ignore
    ) as client:
        assert client.get("/").content == b"OK"

        assert client.post("/").status_code == 405

        assert client.options("/").headers["Allow"] == "GET, OPTIONS"
