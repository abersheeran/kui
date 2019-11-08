from index.view import View
from index.config import logger
from index.responses import TemplateResponse
from index.openapi import models

from utils import db


class Hello(models.Query):
    name = models.StrField(description="name")


class Message(models.Model):
    name = models.StrField(description="your name")
    text = models.StrField(description="what are you want to say?")


class HTTP(View):
    async def get(self, query: Hello):
        """
        welcome page
        """
        return TemplateResponse(
            "home.html",
            {"request": self.request, "db": db.some_db_settings, "name": query.name},
        )

    async def post(self, body: Message):
        """
        echo your message

        just echo your message, hello world.
        """
        return {"message": body.data}, 200, {"server": "index.py"}
