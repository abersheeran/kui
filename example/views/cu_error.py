from indexpy.http import HTTPView
from indexpy.test import TestView

from example.responses import Error


class HTTP(HTTPView):
    def get(self):
        return Error(
            code=1, title="Error title", message="Something went wrong with the server."
        )


class Test(TestView):
    def test_valueerror(self):
        resp = self.client.get()
        assert resp.json() == dict(
            code=1, title="Error title", message="Something went wrong with the server."
        )
