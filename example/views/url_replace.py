from indexpy import Config
from indexpy.http import HTTPView
from indexpy.test import TestView


class HTTP(HTTPView):
    async def get(self):
        return "Nothing"


class Test(TestView):
    def test_url_replace(self):
        resp = self.client.get()
        assert resp.status_code == 200
        assert resp.text == "Nothing"
