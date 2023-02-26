import httpx

from kui.wsgi import HttpView, Kui


def test_http_view():
    app = Kui()

    @app.router.http("/")
    class Home(HttpView):
        @classmethod
        def get(cls):
            return "OK"

    with httpx.Client(app=app, base_url="http://testServer") as client:
        assert client.get("/").content == b"OK"

        assert client.post("/").status_code == 405

        assert client.options("/").headers["Allow"] == "GET, OPTIONS"
