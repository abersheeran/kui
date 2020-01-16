from asyncio import sleep

from index.view import View
from index.test import TestView
from index.background import after_response, finished_response
from index.config import logger


@after_response
def only_print(message: str) -> None:
    logger.debug(message)


class HTTP(View):
    async def get(self):
        only_print("world")
        logger.debug("hello")
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
