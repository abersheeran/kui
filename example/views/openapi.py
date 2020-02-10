from starlette.testclient import TestClient
from indexpy import Index
from indexpy.test import TestView


class Test(TestView):
    def test_get(self):
        resp = TestClient(Index()).get("/openapi/get")
        assert resp.status_code == 200
