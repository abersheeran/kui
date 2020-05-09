Index 使用 [pydantic](https://pydantic-docs.helpmanual.io/) 用于更轻松的解析 HTTP 请求信息，并为之绑定了一套生成 OpenAPI 文档的程序。

## OpenAPI文档

!!! tip
    如果你不想要查看生成的文档，那么这一步不是必须的。

将 `indexpy.openapi.application.OpenAPI` 挂载进 index 中。

```python
from indexpy import Index
from indexpy.openapi.application import OpenAPI

app = Index()

app.mount(
    "/openapi",
    OpenAPI("index.py example", "just a example, power by index.py", "0.1.0"),
    "asgi"
)
```

启动 index，访问你服务上 `/openapi/` 即可看到生成的文档。

### `__doc__`

对于所有可处理 HTTP 请求的方法，它们的 `__doc__` 都会用于生成 OpenAPI 文档。

第一行将被当作概要描述，所以尽量简明扼要，不要太长。

空一行之后，后续的文字都会被当作详细介绍，被安置在 OpenAPI 文档中。

同样的，所有 Model 的 `__doc__` 也会被当作对应的描述安置在生成的文档中。

### Tags

OpenAPI 的 Tags 是一个有用的功能，在 Index 里，你可以通过如下方式来指定 URL 的 tags

```python
app.mount(
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
    ),
    "asgi",
)
```

## 解析请求

一般来说，从 HTTP 请求中传递参数的位置有五个——`path`、`query`、`header`、`cookie`、`body`。但 Index 的设计中，并没有给路径参数(`path`)留下位置，故只有后四种可被 Index 处理。*(可以像使用 PHP 一样用 Nginx 把 query 参数转为 path 参数，但没必要)*

如下例所示，只需要在视图函数中增加对应名称的参数即可使用更 Python 的方式去解析 HTTP 请求。

```python
from indexpy.http import HTTPView
from indexpy.test import TestView
from indexpy.http.responses import TemplateResponse
from indexpy.openapi import describe
from pydantic import BaseModel


class Hello(BaseModel):
    name: str = models.Field("Aber", description="your name")


class Message(BaseModel):
    """your message"""

    name: str = models.Field(..., description="your name")
    text: str = models.Field(..., description="what are you want to say?")


class HTTP(HTTPView):
    async def get(self, query: Hello):
        """
        welcome page
        """
        return TemplateResponse(
            "home.html",
            {"request": self.request, "name": query.name},
        )

    async def post(self, body: Message):
        """
        echo your message

        just echo your message.
        """
        return {"message": body.dict()}, 200, {"server": "index.py"}
```

### 自定义错误返回

当请求不满足编写的 Model 限制的条件时，Index 将直接返回 400 以及对应的错误信息，请求不会到达视图函数。但你可以通过重写 View 类中的 `catch_validation_error` 函数来自定义处理解析错误。默认的定义如下

```python
async def catch_validation_error(
    self, exception: ValidationError
) -> typing.Union[Response, typing.Tuple]:
    """
    Used to handle request parsing errors
    """
    return {"error": exception.errors()}, 400
```

### 描述上传文件

由于 [pydantic](https://pydantic-docs.helpmanual.io/usage/types/) 中没有上传文件类型，所以当需要描述文件上传的 model 时，需要使用 `indexpy.openapi.types.File` 来进行类型标注。

!!! notice
    此类型不可以用于描述响应值

## 绑定响应

为了描述不同状态码的响应结果，Index 使用装饰器描述，而不是类型注解。既可以使用 models 描述响应(仅支持 application/json)，亦可以直接传递 OpenAPI 文档字符串（当你不想返回一个 application/json 类型的响应时）。

!!! notice
    此功能到目前为止，除生成OpenAPI文档的作用外，无其他作用。**未来或许会增加 mock 功能。**

```python
from indexpy.http import HTTPView
from indexpy.test import TestView
from indexpy.http.responses import TemplateResponse
from indexpy.openapi import describe
from pydantic import BaseModel


class Hello(BaseModel):
    name: str = models.Field("Aber", description="your name")


class Message(BaseModel):
    """your message"""

    name: str = models.Field(..., description="your name")
    text: str = models.Field(..., description="what are you want to say?")


class MessageResponse(BaseModel):
    """message response"""

    message: Message


class HTTP(HTTPView):
    @describe(
        200,
        """
        image/png:
            schema:
                type: string
                format: binary
        """,
    )
    @describe(
        403,
        """text/plain:
            schema:
                type: string
            example:
                pong
        """,
    )
    async def get(self, query: Hello):
        """
        welcome page
        """
        ...

    @describe(200, MessageResponse)
    @describe(201, None)
    async def post(self, body: Message):
        """
        echo your message

        just echo your message.
        """
        return {"message": body.dict()}, 200, {"server": "index.py"}
```
