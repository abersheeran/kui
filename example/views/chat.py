from indexpy import g
from indexpy.view import View, SocketView
from indexpy.responses import TemplateResponse
from indexpy.test import TestView


class HTTP(View):
    def get(self):
        return TemplateResponse("chat.html", {"request": self.request})


if not hasattr(g, "users"):
    g.users = []


class Socket(SocketView):

    encoding = "text"

    async def broadcast(self, message):
        for user in g.users:
            await user.send_json(message)

    async def on_connect(self):
        """Override to handle an incoming websocket connection"""
        await self.websocket.accept()
        await self.broadcast(
            {"from": "system", "message": f"欢迎{self.websocket.client}入场"}
        )
        g.users.append(self.websocket)

    async def on_receive(self, data):
        """Override to handle an incoming websocket message"""
        await self.broadcast({"from": self.websocket.client, "message": data})

    async def on_disconnect(self, close_code):
        """Override to handle a disconnecting websocket"""
        g.users.remove(self.websocket)
        await self.websocket.close(code=close_code)
        await self.broadcast(
            {"from": "system", "message": f"欢送{self.websocket.client}离场"}
        )


class Test(TestView):
    def test_get_html(self) -> None:
        assert self.client.get().status_code == 200

    def test_chat(self) -> None:

        with self.client.websocket_connect() as ws:
            ws.send_text("hello")
            assert ws.receive_json()["message"] == "hello"
