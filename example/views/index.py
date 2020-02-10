from indexpy.view import View
from indexpy.test import TestView
from indexpy.responses import TemplateResponse
from indexpy.openapi import models, describe

from utils import db


class Hello(models.Model):
    name: str = models.Field("Aber", description="your name")


class Message(models.Model):
    """your message"""

    name: str = models.Field(..., description="your name")
    text: str = models.Field(..., description="what are you want to say?")


class MessageResponse(models.Model):
    """message response"""

    message: Message


class HTTP(View):
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
    def test_get(self):
        resp = self.client.get()
        assert resp.status_code == 200
        resp = self.client.get(params={"name": "darling"})
        assert resp.status_code == 200

    def test_post(self):
        resp = self.client.post()
        assert resp.status_code == 400
        resp = self.client.post(data={"name": "Aber", "text": "message"})
        assert resp.status_code == 200

    def test_list_response(self):
        resp = self.client.put()
        assert resp.json() == ["h",] * 10
