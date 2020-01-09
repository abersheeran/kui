from asyncio import sleep

from index.view import View
from index.test import TestView
from index.background import after_response
from index.config import logger


@after_response
def only_print(message: str) -> None:
    logger.debug(message)


class HTTP(View):
    async def get(self):
        only_print("world")
        await sleep(1.5)
        logger.debug("hello")
        return ""


class Test(TestView):
    def test_background(self) -> None:
        resp = self.client.get()
        assert resp.status_code == 200
        assert resp.content == b""

    def test_websocket_dontfound(self) -> None:
        from starlette.exceptions import HTTPException

        try:
            self.client.websocket_connect()
        except HTTPException as exc:
            assert exc.status_code == 404
