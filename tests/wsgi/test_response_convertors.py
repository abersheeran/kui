from pathlib import Path

from baize.wsgi import Files, Response
from httpx import Client
from pydantic import BaseModel

from kui.wsgi import Kui


def test_pydantic_base_model():
    class Message(BaseModel):
        message: str

    app = Kui()

    @app.router.http("/message")
    def message():
        return Message(message="Hello, World!")

    @app.router.http("/{_:any}")
    def static_files():
        return Files(Path(__file__).absolute().parent, handle_404=Response(404))

    client = Client(app=app, base_url="http://testserver")
    response = client.get("/message")
    assert response.status_code == 200
    assert response.json() == {"message": "Hello, World!"}

    response = client.get("/test_response_convertors.py")
    assert response.status_code == 200
