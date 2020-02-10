from indexpy import Config
from indexpy.view import View
from indexpy.test import TestView


class HTTP(View):
    async def get(self):
        return str(Config())


class Test(TestView):
    def test_config(self):
        assert self.client.get().status_code == 200
