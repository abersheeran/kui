import sys
from http import HTTPStatus
from typing import List

import pytest
from pydantic import BaseModel
from starlette.testclient import TestClient

from indexpy import Index
from indexpy.http import HTTPView, Path
from indexpy.openapi import describe_extra_docs, describe_response
from indexpy.openapi.application import OpenAPI
from indexpy.routing import HttpRoute, SubRoutes


@pytest.mark.skipif(
    sys.version_info < (3, 7),
    reason="The str behavior of typing.List has changed after 3.7",
)
def test_openapi_page():
    app = Index()
    app.router.extend(
        SubRoutes("/openapi", OpenAPI("Title", "description", "1.0").routes)
    )

    @app.router.http("/hello", method="get")
    @describe_response(200, content=List[str])
    async def hello(request):
        """
        hello

        接口描述
        """
        pass

    class Username(BaseModel):
        name: str

    @app.router.http("/path/{name}", method="get")
    async def path(request, name: str = Path(...)):
        pass

    @app.router.http("/http-view")
    class HTTPClass(HTTPView):
        @describe_response(
            HTTPStatus.OK,
            content={
                "text/html": {
                    "schema": {"type": "string"},
                }
            },
        )
        async def get(self):
            """
            ...

            ......
            """

        @describe_response(HTTPStatus.CREATED, content=Username)
        async def post(self):
            """
            ...

            ......
            """

        @describe_response(HTTPStatus.NO_CONTENT)
        async def delete(self):
            """
            ...

            ......
            """

    def just_middleware(endpoint):
        describe_extra_docs(
            endpoint,
            {
                "parameters": [
                    {
                        "name": "Authorization",
                        "in": "header",
                        "description": "JWT Token",
                        "required": True,
                        "schema": {"type": "string"},
                    }
                ]
            },
        )
        return endpoint

    middleware_routes = SubRoutes(
        "/middleware",
        [
            HttpRoute("/path/{name}", path, "middleware-path", method="get"),
            HttpRoute("/http-view", HTTPClass, "middleware-HTTPClass"),
        ],
        http_middlewares=[just_middleware],
    )

    app.router.extend(middleware_routes)

    client = TestClient(app)
    assert client.get("/openapi/docs").status_code == 200
    openapi_docs_text = client.get("/openapi/docs").text

    _ = """definitions: {}
info:
  description: description
  title: Title
  version: '1.0'
openapi: 3.0.0
paths:
  /hello:
    get:
      description: 接口描述
      responses:
        200:
          content:
            application/json:
              schema:
                items:
                  type: string
                title: ParsingModel[List[str]]
                type: array
          description: Request fulfilled, document follows
      summary: hello
  /http-view:
    delete:
      description: '......'
      parameters: &id001
      - description: JWT Token
        in: header
        name: Authorization
        required: true
        schema:
          type: string
      responses:
        204:
          description: Request fulfilled, nothing follows
      summary: '...'
    get:
      description: '......'
      parameters: *id001
      responses:
        200:
          content: &id002
            text/html:
              schema:
                type: string
          description: Request fulfilled, document follows
      summary: '...'
    post:
      description: '......'
      parameters: *id001
      responses:
        201:
          content:
            application/json:
              schema:
                properties:
                  name:
                    title: Name
                    type: string
                required:
                - name
                title: Username
                type: object
          description: Document created, URL follows
      summary: '...'
  /middleware/http-view:
    delete:
      description: '......'
      parameters: *id001
      responses:
        204:
          description: Request fulfilled, nothing follows
      summary: '...'
    get:
      description: '......'
      parameters: *id001
      responses:
        200:
          content: *id002
          description: Request fulfilled, document follows
      summary: '...'
    post:
      description: '......'
      parameters: *id001
      responses:
        201:
          content:
            application/json:
              schema:
                properties:
                  name:
                    title: Name
                    type: string
                required:
                - name
                title: Username
                type: object
          description: Document created, URL follows
      summary: '...'
  /middleware/path/{name}:
    get:
      parameters:
      - description: ''
        in: path
        name: name
        required: true
        schema:
          title: Name
          type: string
      - &id003
        description: JWT Token
        in: header
        name: Authorization
        required: true
        schema:
          type: string
      responses:
        422:
          content:
            application/json:
              schema:
                items:
                  properties:
                    loc:
                      description: error field
                      items:
                        type: string
                      title: Loc
                      type: array
                    msg:
                      description: error message
                      title: Msg
                      type: string
                    type:
                      description: error type
                      title: Type
                      type: string
                  required:
                  - loc
                  - type
                  - msg
                  type: object
                type: array
          description: Failed to verify request parameters
  /path/{name}:
    get:
      parameters:
      - description: ''
        in: path
        name: name
        required: true
        schema:
          title: Name
          type: string
      - *id003
      responses:
        422:
          content:
            application/json:
              schema:
                items:
                  properties:
                    loc:
                      description: error field
                      items:
                        type: string
                      title: Loc
                      type: array
                    msg:
                      description: error message
                      title: Msg
                      type: string
                    type:
                      description: error type
                      title: Type
                      type: string
                  required:
                  - loc
                  - type
                  - msg
                  type: object
                type: array
          description: Failed to verify request parameters
servers:
- description: Current server
  url: http://testserver
tags: []
"""
    assert openapi_docs_text == _
