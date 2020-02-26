from indexpy.test import TestView


class Test(TestView):
    def test_openapi(self):
        assert self.client.get().status_code == 200
