from index.view import View, SocketView
from index.responses import TemplateResponse
from index.utils import Singleton
from index.test import TestView


class HTTP(View):
    def get(self):
        return TemplateResponse("chat.html", {"request": self.request})


try:
    users
except NameError:
    users = []


class Socket(SocketView, metaclass=Singleton):

    encoding = "text"

    async def broadcast(self, message):
        for user in users:
            await user.send_json(message)

    async def on_connect(self, websocket):
        """Override to handle an incoming websocket connection"""
        await websocket.accept()
        await self.broadcast({"from": "system", "message": f"欢迎{websocket.client}入场"})
        users.append(websocket)

    async def on_receive(self, websocket, data):
        """Override to handle an incoming websocket message"""
        await self.broadcast({"from": websocket.client, "message": data})

    async def on_disconnect(self, websocket, close_code):
        """Override to handle a disconnecting websocket"""
        users.remove(websocket)
        await websocket.close(code=close_code)
        await self.broadcast({"from": "system", "message": f"欢送{websocket.client}离场"})


class Test(TestView):
    def test_chat(self) -> None:

        with self.client.websocket_connect() as ws:
            ws.send_text("hello")
            assert ws.receive_json()["message"] == "hello"
