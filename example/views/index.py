from index import templates, Config
from index.view import View
from index.config import logger

from views.utils.db import some_db_settings


class HTTP(View):

    def get(self):
        print("get repsonse")
        return templates.TemplateResponse("home.html", {"request": self.request, "db": some_db_settings})


    def post(self):
        return {"message": "some error in server"}, 500, {"server": "index.py"}
