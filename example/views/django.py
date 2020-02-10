from starlette.testclient import TestClient
from indexpy.test import TestView
from indexpy import Index


class Test(TestView):
    def test_django(self):
        resp = self.client.get()
        assert resp.status_code == 404

    def test_django_admin(self):
        client = TestClient(Index())
        resp = client.get("/django/admin/")
        assert resp.status_code == 200, resp.status_code

    def test_wsgi_websocket(self):
        from starlette.websockets import WebSocketDisconnect

        client = TestClient(Index())
        try:
            resp = client.websocket_connect("/django/")
        except WebSocketDisconnect as e:
            assert e.code == 1001
        else:
            assert False, "Must be raise WebSocketDisconnect"
