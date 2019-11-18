from index.view import View
from index.responses import TemplateResponse
from index.openapi import models, bindresponse

from utils import db


class Hello(models.Model):
    name = models.StrField(description="name")


class Message(models.Model):
    """your message"""

    name = models.StrField(description="your name")
    text = models.StrField(description="what are you want to say?")


class MessageResponse(models.Model):
    """message response"""

    message = models.ModelField(Message)


class HTTP(View):
    async def get(self, query: Hello):
        """
        welcome page
        """
        return TemplateResponse(
            "home.html",
            {"request": self.request, "db": db.some_db_settings, "name": query.name},
        )

    @bindresponse(200, MessageResponse)
    @bindresponse(201, None)
    async def post(self, body: Message):
        """
        echo your message

        just echo your message.
        """
        return {"message": body.data}, 200, {"server": "index.py"}
