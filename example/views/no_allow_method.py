from indexpy.http import HTTPView
from indexpy.test import TestView


class HTTP(HTTPView):
    pass


class Test(TestView):
    def test_not_allow_method(self):
        assert self.client.get().status_code == 405
