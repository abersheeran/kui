from __future__ import annotations

import asyncio
import json
from hashlib import md5

from ..openapi import OpenAPI as _OpenAPI
from .requests import request
from .responses import HTMLResponse, JSONResponse
from .routing import HttpRoute, Routes


class OpenAPI(_OpenAPI):
    @property
    def routes(self) -> Routes:
        async def redirect():
            return request.url.replace(path=request.url.path + "/")

        async def template():
            return HTMLResponse(self.html_template)

        async def json_docs():
            openapi = self.create_docs(request)
            return JSONResponse(
                openapi,
                headers={
                    "hash": md5(json.dumps(openapi).encode()).hexdigest(),
                    "reload": str(self.reload).lower(),
                },
            )

        async def heartbeat():
            async def g():
                openapi = self.create_docs(request)
                yield {
                    "id": md5(json.dumps(openapi).encode()).hexdigest(),
                    "data": json.dumps(openapi),
                }
                while not request.app.should_exit:
                    await asyncio.sleep(0.5)

            return g()

        return Routes(
            HttpRoute("", redirect, name=None),
            HttpRoute("/", template, name=None),
            HttpRoute("/json", json_docs, name=None),
            HttpRoute("/heartbeat", heartbeat, name=None),
        )
