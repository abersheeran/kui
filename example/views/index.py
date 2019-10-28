from index.view import View
from index.config import logger
from index.responses import TemplateResponse

from utils import db


class HTTP(View):

    async def get(self):
        logger.info("get repsonse")
        from index import app
        print(app.router.apps)
        return TemplateResponse("home.html", {"request": self.request, "db": db.some_db_settings})

    async def post(self):
        return {"message": "some error in server"}, 200, {"server": "index.py"}
