import httpx

from kui.wsgi import HttpView, Kui


def test_http_view():
    app = Kui()

    @app.router.http("/")
    class Home(HttpView):
        @staticmethod
        def get():
            return "OK"

    with httpx.Client(app=app, base_url="http://testServer") as client:
        assert client.get("/").content == b"OK"

        assert client.post("/").status_code == 405
