from indexpy import Config
from indexpy.view import View
from indexpy.test import TestView


class HTTP(View):
    async def get(self):
        return "Nothing"


class Test(TestView):
    def test_url_replace(self):
        resp = self.client.get()
        assert resp.status_code == 200
        assert resp.text == "Nothing"
