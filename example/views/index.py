from indexpy.http import HTTPView
from indexpy.test import TestView
from indexpy.http.responses import TemplateResponse
from indexpy.openapi import describe
from pydantic import BaseModel, Field

from utils import db


class Hello(BaseModel):
    name: str = "Aber"


class Message(BaseModel):
    """your message"""

    name: str = Field(..., description="your name")
    text: str = Field(..., description="what are you want to say?")


class MessageResponse(BaseModel):
    """message response"""

    message: Message


class HTTP(HTTPView):
    @describe(
        200,
        """
        text/html:
            schema:
                type: string
        """,
    )
    async def get(self, query: Hello):
        """
        welcome page
        """
        return TemplateResponse(
            "home.html",
            {"request": self.request, "db": db.some_db_settings, "name": query.name},
        )

    @describe(200, MessageResponse)
    @describe(201, None)
    async def post(self, body: Message):
        """
        echo your message

        just echo your message.
        """
        return {"message": body.dict()}, 200, {"server": "index.py"}

    async def put(self):
        return ["h",] * 10


class Test(TestView):
    def test_get_0(self):
        resp = self.client.get()
        assert resp.status_code == 200

    def test_get_1(self):
        resp = self.client.get(params={"name": "darling"})
        assert resp.status_code == 200

    def test_post_0(self):
        resp = self.client.post()
        assert resp.status_code == 400

    def test_post_1(self):
        resp = self.client.post(data={"name": "Aber", "text": "message"})
        assert resp.status_code == 200

    def test_list_response(self):
        resp = self.client.put()
        assert resp.json() == ["h",] * 10
