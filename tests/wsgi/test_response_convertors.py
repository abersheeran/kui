from pydantic import BaseModel
from kui.wsgi import Kui
from httpx import Client


def test_pydantic_base_model():
    class Message(BaseModel):
        message: str

    app = Kui()

    @app.router.http("/message")
    def message():
        return Message(message="Hello, World!")

    @app.router.http("/static/{_:any}")
    def static_files():
        return Files(Path(__file__).absolute().parent)

    client = Client(app=app, base_url="http://testserver")
    response = client.get("/message")
    assert response.status_code == 200
    assert response.json() == {"message": "Hello, World!"}

    response = client.get("/static/test_response_convertors.py")
    assert response.status_code == 200
