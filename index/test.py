from starlette.testclient import TestClient
from starlette.types import ASGIApp


class TestView:

    def __init__(self, app: ASGIApp) -> None:
        self.client = TestClient(app)

    def http(self, app: ASGIApp) -> None:
        pass
