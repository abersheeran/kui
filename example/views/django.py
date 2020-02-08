from starlette.testclient import TestClient
from index.test import TestView
from index import app


class Test(TestView):
    def test_django(self):
        resp = self.client.get()
        assert resp.status_code == 404

    def test_django_admin(self):
        client = TestClient(app)
        resp = client.get("/django/admin/")
        assert resp.status_code == 200

    def test_wsgi_websocket(self):
        from starlette.websockets import WebSocketDisconnect

        client = TestClient(app)
        try:
            resp = client.websocket_connect("/django/")
        except WebSocketDisconnect as e:
            assert e.code == 1001
        else:
            assert False, "Must be raise WebSocketDisconnect"
