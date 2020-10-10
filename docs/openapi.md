Index 使用 [pydantic](https://pydantic-docs.helpmanual.io/) 用于更轻松的解析 HTTP 请求信息，并为之绑定了一套生成 OpenAPI 文档的程序。这与 Index 核心并不是强耦合的，所以你可以选择使用，也可以选择不使用。

## 显示 OpenAPI 文档

将 `indexpy.openapi.application.OpenAPI` 挂载进 index 中。

```python
from indexpy import Index
from indexpy.openapi import OpenAPI

app = Index()

app.router.extend(
    SubRoutes("/openapi", OpenAPI("Title", "description", "1.0").routes)
)
```

启动 index，访问你服务上 `/openapi/` 即可看到生成的文档。

## 接口描述

对于所有可处理 HTTP 请求的方法，它们的 `__doc__` 都会用于生成 OpenAPI 文档。

第一行将被当作概要描述，所以尽量简明扼要，不要太长。

空一行之后，后续的文字都会被当作详细介绍，被安置在 OpenAPI 文档中。

例如：

```python
async def get(request):
    """
    获取用户信息

    此接口用于获取用户信息，然后我就不知道该编什么话了，总之这一段都是接口描述，而空的一行的上面是接口标题。
    """
    ...
```

### 请求

对于所有可处理 HTTP 请求的方法，均可以接受五种参数：`path`、`body`、`query`、`header`、`cookie`。

使用继承自 `pydantic.BaseModel` 的类作为类型注解即可做到自动参数校验以及生成请求格式文档。

### 响应

为了描述不同状态码的响应结果，Index 使用装饰器描述，而不是类型注解。既可以使用 models 描述响应(仅支持 application/json)，亦可以直接传递 OpenAPI 文档字符串（当你不想返回一个 application/json 类型的响应时）。

!!! notice
    此功能到目前为止，除生成OpenAPI文档的作用外，无其他作用。**未来或许会增加 mock 功能。**

### 样例

```python
from indexpy.http import HTTPView
from indexpy.http.responses import TemplateResponse
from indexpy.openapi import describe
from pydantic import BaseModel, Field


class Hello(BaseModel):
    name: str = "Aber"


class Message(BaseModel):
    """your message"""

    name: str = Field(..., description="your name")
    text: str = Field(..., description="what are you want to say?")


class MessageResponse(BaseModel):
    """message response"""

    message: Message


class HTTP(HTTPView):
    @describe(
        200,
        """
        text/html:
            schema:
                type: string
        """,
    )
    async def get(self, query: Hello):
        """
        welcome page
        """
        return f"welcome, {query.name}."

    @describe(200, MessageResponse)
    @describe(201, None)
    async def post(self, body: Message):
        """
        echo your message

        just echo your message.
        """
        return {"message": body.dict()}, 200, {"server": "index.py"}
```

## Tags

OpenAPI 的 Tags 是一个有用的功能，在 Index 里，你可以通过如下方式来指定 URL 的分类标签。

`tags` 参数必须是一个 `dict` 类型，键为标签名。值需要包含 `description`，用于描述此标签；`paths` 是 URL 列表，如果 URL 包含路径参数，直接使用不带 `:type` 的字符串即可。

```python
app.mount_asgi(
    "/openapi",
    OpenAPI(
        "index.py example",
        "just a example, power by index.py",
        __version__,
        tags={
            "something": {
                "description": "test over two tags in one path",
                "paths": ["/about/", "/file", "/"],
            },
            "about": {"description": "about page", "paths": ["/about/", "/about/me"]},
            "file": {"description": "get/upload file api", "paths": ["/file"]},
        },
    )
)
```
