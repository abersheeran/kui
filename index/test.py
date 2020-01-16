import typing
from functools import partial

import requests
from requests import Response
from starlette.testclient import TestClient as _TestClient, ASGI2App, ASGI3App
from starlette.types import ASGIApp

from .values import HTTP_METHOD_NAMES


class TestClient:
    def __init__(
        self,
        app: typing.Union[ASGI2App, ASGI3App],
        uri: str = "",
        base_url: str = "http://testserver",
        raise_server_exceptions: bool = True,
        root_path: str = "",
    ) -> None:
        self.uri = uri
        self.__client = _TestClient(app, base_url, raise_server_exceptions, root_path)

    def get(self, *args, **kwargs) -> Response:
        return self.__client.get(self.uri, *args, **kwargs)

    def options(self, *args, **kwargs) -> Response:
        return self.__client.options(self.uri, *args, **kwargs)

    def head(self, *args, **kwargs) -> Response:
        return self.__client.head(self.uri, *args, **kwargs)

    def post(self, *args, **kwargs) -> Response:
        return self.__client.post(self.uri, *args, **kwargs)

    def put(self, *args, **kwargs) -> Response:
        return self.__client.put(self.uri, *args, **kwargs)

    def patch(self, *args, **kwargs) -> Response:
        return self.__client.patch(self.uri, *args, **kwargs)

    def delete(self, *args, **kwargs) -> Response:
        return self.__client.delete(self.uri, *args, **kwargs)

    def websocket_connect(
        self, subprotocols: typing.Sequence[str] = None, **kwargs: typing.Any
    ) -> typing.Any:
        return self.__client.websocket_connect(
            self.uri, subprotocols=subprotocols, **kwargs
        )

    def __enter__(self) -> requests.Session:
        return self.__client.__enter__()

    def __exit__(self, *args: typing.Any) -> None:
        return self.__client.__exit__()


class TestView:
    def __init__(self, app: ASGIApp, uri: str) -> None:
        self.client: TestClient = self.client if hasattr(
            self, "client"
        ) else TestClient(app, uri)

        if not self.client.uri:
            self.client.uri = uri

    @property
    def all_test(self) -> typing.List[typing.Callable]:
        return [
            getattr(self, name)
            for name in dir(self)
            if name.startswith("test_") and callable(getattr(self, name))
        ]
