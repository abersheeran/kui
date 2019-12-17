from index.view import View


class HTTP(View):
    async def get(self):
        """
        about me
        """
        return "about me"
