from indexpy.test import TestView


class Test(TestView):
    def test_notfound(self):
        resp = self.client.get()
        assert resp.status_code == 404
