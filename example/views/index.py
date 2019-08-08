from index import Config
from index.view import View
from index.config import logger
from index.responses import TemplateResponse

from views.utils import db
from views.utils.db import some_db_settings


class HTTP(View):

    def get(self):
        logger.info("get repsonse")
        return TemplateResponse("home.html", {"request": self.request, "db": db.some_db_settings})

    def post(self):
        return {"message": "some error in server"}, 500, {"server": "index.py"}
