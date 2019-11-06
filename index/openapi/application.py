import os
import typing
import importlib
from inspect import signature

from starlette.types import Scope, Receive, Send
from starlette.endpoints import HTTPEndpoint, Request, Response
from starlette.exceptions import HTTPException

from index.responses import JSONResponse
from index.config import config


def get_views():
    views_path = os.path.join(config.path, "views").replace("\\", "/")
    for root, dirs, files in os.walk(views_path):
        for file in files:
            if not file.endswith(".py"):
                continue
            if file == "__init__.py":
                continue
            abspath = os.path.join(root, file)
            relpath = os.path.relpath(abspath, config.path).replace("\\", "/")
            module_name = relpath[:-3].replace("/", ".")
            module = importlib.import_module(module_name)
            if abspath.startswith(views_path):
                yield module_name.replace(".", "/").replace("views", ""), module


class OpenAPI(HTTPEndpoint):
    def __init__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            raise HTTPException(404)
        super().__init__(scope, receive, send)

    def get(self, request: Request) -> Response:
        return self.post(request)

    def post(self, request: Request) -> Response:
        for path, view in get_views():
            viewclass = view.HTTP()
            for method in viewclass.allowed_methods():
                if method == "OPTIONS":
                    continue
                method = method.lower()
                sig = signature(getattr(viewclass, method))
                print(path, method, sig)
        return Response("")
