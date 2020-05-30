from indexpy.test import TestView


class Test(TestView):
    def test_find_template(self):
        resp = self.client.get()
        assert resp.status_code == 200
        assert resp.text == "other html"
