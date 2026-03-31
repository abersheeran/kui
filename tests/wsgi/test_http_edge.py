import httpx
from httpx import Client
from typing_extensions import Annotated

from kui.wsgi import Body, Kui


def test_wsgi_unsupported_media_type():
    app = Kui()

    @app.router.http.post("/")
    def handler(data: Annotated[dict, Body(exclusive=True)]):
        return data

    with Client(
        transport=httpx.WSGITransport(app=app),  # type: ignore[arg-type]
        base_url="http://testserver",
    ) as client:
        response = client.post(
            "/", content=b"raw", headers={"content-type": "application/xml"}
        )

    assert response.status_code == 415
