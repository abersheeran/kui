from index import templates
from index.views import View


class HTTP(View):

    def get(self, request):
        return templates.TemplateResponse("home.html", {"request": request})

    def post(self, request):
        return templates.TemplateResponse("home.html", {"request": request})
