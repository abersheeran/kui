from index import templates
from index.views import View
from starlette.responses import PlainTextResponse


class HTTP(View):

    def post(self, request):
        return templates.TemplateResponse("home.html", {"request": request})
