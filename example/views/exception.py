from indexpy.view import View
from indexpy.test import TestView
from indexpy.background import finished_response


@finished_response
def onlytest():
    _ = ...


class HTTP(View):
    def get(self):
        onlytest()
        raise ValueError("some error")


class Test(TestView):
    def test_valueerror(self):
        resp = self.client.get()
        assert resp.text == "Something went wrong with the server."
