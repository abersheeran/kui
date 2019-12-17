import typing
from functools import partial

from starlette.testclient import TestClient
from starlette.types import ASGIApp

from .view import HTTP_METHOD_NAMES


class TestView:
    def __init__(self, app: ASGIApp, uri: str) -> None:
        self.client = self.client if hasattr(self, "client") else TestClient(app)
        for method in HTTP_METHOD_NAMES:
            if not hasattr(self.client, method):
                continue
            setattr(self.client, method, partial(getattr(self.client, method), uri))

        self.client.websocket_connect = partial(self.client.websocket_connect, uri)

    @property
    def all_test(self) -> typing.List[typing.Callable]:
        return [
            getattr(self, name)
            for name in dir(self)
            if name.startswith("test_") and callable(getattr(self, name))
        ]
