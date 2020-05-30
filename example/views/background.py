from indexpy.http import HTTPView
from indexpy.test import TestView
from indexpy.http import after_response, finished_response


@finished_response
def onlytest():
    _ = ...


@after_response
def only_print(message: str) -> None:
    print(message)


class HTTP(HTTPView):
    async def get(self):
        only_print("world")
        print("hello")
        onlytest()
        return ""


class Test(TestView):
    def test_background(self) -> None:
        resp = self.client.get()
        assert resp.status_code == 200
        assert resp.content == b""

    def test_websocket_dontfound(self) -> None:
        from starlette.testclient import WebSocketDisconnect

        try:
            self.client.websocket_connect()
            assert False, "websocket must disconnect"
        except WebSocketDisconnect:
            pass
