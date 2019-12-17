from index.view import View
from index.test import TestView
from index.responses import TemplateResponse
from index.openapi import models, describe

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
