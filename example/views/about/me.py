from index.view import View
from index.test import TestView


class HTTP(View):
    async def get(self):
        """
        about me
        """
        return "about me"


class Test(TestView):
    def test_get(self):
        resp = self.client.get()
        assert resp.status_code == 200
        assert resp.text == "about me"
