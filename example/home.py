from index import templates, Config
from index.views import View


class HTTP(View):

    def get(self):
        return templates.TemplateResponse("home.html", {"request": self.request})

    def post(self):
        return {"message": "some error in server"}, 500, {"server": "index.py"}
