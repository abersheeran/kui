from starlette.testclient import TestClient
from index import app
from index.test import TestView


class Test(TestView):
    def test_get(self):
        resp = TestClient(app).get("/openapi/get")
        assert resp.status_code == 200
