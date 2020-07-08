from indexpy.http import HTTPView
from indexpy.test import TestView


class HTTP(HTTPView):
    async def get(self):
        raise NotImplementedError("error for test")


class Test(TestView):
    def test_get(self):
        resp = self.client.get()
        assert resp.status_code == 500
        assert resp.text == "NotImplementedError in /exc/*"
