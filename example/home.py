from index import templates, Config
from index.views import View

from utils.db import some_db_settings


class HTTP(View):

    def get(self):
        return templates.TemplateResponse("home.html", {"request": self.request, "db": some_db_settings})

    def post(self):
        return {"message": "some error in server"}, 500, {"server": "index.py"}
