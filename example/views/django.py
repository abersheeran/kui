from starlette.testclient import TestClient
from index.test import TestView
from index import app


class Test(TestView):
    def test_django(self):
        resp = self.client.get()
        assert resp.status_code == 404

    def test_django_admin(self):
        with TestClient(app) as client:
            resp = client.get("/django/admin/")
            assert resp.status_code == 200
