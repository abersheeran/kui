from __future__ import annotations

import json
import time
from hashlib import md5

from ..openapi import OpenAPI as _OpenAPI
from .requests import request
from .responses import HTMLResponse, JSONResponse
from .routing import HttpRoute, Routes


class OpenAPI(_OpenAPI):
    @property
    def routes(self) -> Routes:
        def redirect():
            return request.url.replace(path=request.url.path + "/")

        def template():
            return HTMLResponse(self.html_template)

        def json_docs():
            openapi = self.create_docs(request)
            return JSONResponse(
                openapi,
                headers={
                    "hash": md5(json.dumps(openapi).encode()).hexdigest(),
                    "reload": str(self.reload).lower(),
                },
            )

        def heartbeat():
            def g():
                openapi = self.create_docs(request)
                yield {
                    "id": md5(json.dumps(openapi).encode()).hexdigest(),
                    "data": json.dumps(openapi),
                }
                while not request.app.should_exit:
                    time.sleep(0.5)

            return g()

        return Routes(
            HttpRoute("", redirect, name=None),
            HttpRoute("/", template, name=None),
            HttpRoute("/json", json_docs, name=None),
            HttpRoute("/heartbeat", heartbeat, name=None),
        )
