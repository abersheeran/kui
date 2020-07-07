from indexpy.http import HTTPView
from indexpy.test import TestView
from indexpy.http import finished_response


@finished_response
def onlytest():
    _ = ...


class HTTP(HTTPView):
    def get(self):
        onlytest()
        raise ValueError("some error")


class Test(TestView):
    def test_valueerror(self):
        resp = self.client.get()
        assert resp.text == "Something went wrong with the server."
