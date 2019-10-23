import os
import typing
import importlib

from starlette.types import Scope, Receive, Send
from starlette.endpoints import HTTPEndpoint, Request, Response
from starlette.exceptions import HTTPException

from index.responses import JSONResponse
from index.config import config


def get_views():
    views_path = os.path.join(config.path, 'views/').replace("\\", "/")
    for root, dirs, files in os.walk(config.path):
        for file in files:
            if not file.endswith(".py"):
                continue
            abspath = os.path.join(root, file).replace("\\", "/")
            module = importlib.import_module(
                abspath[:-3].replace("__init__", "").replace("/", ".")
            )
            if abspath.startswith(views_path):
                yield module


class OpenAPI(HTTPEndpoint):

    def __init__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            raise HTTPException(404)
        super().__init__(scope, receive, send)

    def get(self, request: Request) -> Response:
        return self.post(request)

    def post(self, request: Request) -> Response:
        # TODO
        pass
