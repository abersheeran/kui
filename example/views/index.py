from index.view import View
from index.config import logger
from index.responses import TemplateResponse
from index.openapi import models

from utils import db


class Query(models.Model):
    name = models.StrField()


class HTTP(View):
    async def get(self, headers: Query):
        logger.info("get repsonse")
        return TemplateResponse(
            "home.html", {"request": self.request, "db": db.some_db_settings}
        )

    async def post(self):
        return {"message": "some error in server"}, 200, {"server": "index.py"}
