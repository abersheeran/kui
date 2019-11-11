from index.view import View
from index.responses import TemplateResponse
from index.openapi import models
from index.openapi.functions import bindresponse

from utils import db


class Hello(models.QueryModel):
    name = models.StrField(description="name")


class MessageForm(models.FormModel):
    """your message"""

    name = models.StrField(description="your name")
    text = models.StrField(description="what are you want to say?")


class _MessageResponse(models.JsonRespModel):
    """your message"""

    name = models.StrField(description="your name")
    text = models.StrField(description="what are you want to say?")


class MessageResponse(models.JsonRespModel):
    """message response"""

    message = models.ModelField(_MessageResponse)


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
    async def post(self, body: MessageForm):
        """
        echo your message

        just echo your message, hello world.
        """
        return {"message": body.data}, 200, {"server": "index.py"}
