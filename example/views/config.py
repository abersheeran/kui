from indexpy import Config
from indexpy.http import HTTPView
from indexpy.test import TestView


class HTTP(HTTPView):
    async def get(self):
        return str(Config())


class Test(TestView):
    def test_config(self):
        assert self.client.get().status_code == 200
