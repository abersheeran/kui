from index.views import View


class HTTP(View):

    def get(self):
        return "about me"
