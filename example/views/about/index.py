from index.view import View


class HTTP(View):

    async def get(self):
        return "about"
