Index 使用 [pydantic](https://pydantic-docs.helpmanual.io/) 用于更轻松的解析 HTTP 请求信息，并为之绑定了一套生成 OpenAPI 文档的程序。

## OpenAPI文档

!!! tip
    如果你不想要查看生成的文档，那么这一步不是必须的。

在 `mounts.py` 中写入如下内容，可将 `index.openapi.application.OpenAPI` 挂载进 index 中。

```python
from index import app
from index.openapi.application import OpenAPI

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

## 解析请求

一般来说，从 HTTP 请求中传递参数的位置有五个——`path`、`query`、`header`、`cookie`、`body`。但 Index 的设计中，并没有给路径参数(`path`)留下位置，故只有后四种可被 Index 处理。*(可以像使用 PHP 一样用 Nginx 把 query 参数转为 path 参数，但没必要)*

如下例所示，只需要在视图函数中增加对应名称的参数即可使用更 Python 的方式去解析 HTTP 请求。
当请求不满足编写的 Model 限制的条件时，Index 将直接返回 400 以及对应的错误信息，请求不会到达视图函数，但你可以在路径上的任意一个中间件中捕捉这类返回。

```python
from index.view import View
from index.test import TestView
from index.responses import TemplateResponse
from index.openapi import models, describe


class Hello(models.Model):
    name: str = models.Field("Aber", description="your name")


class Message(models.Model):
    """your message"""

    name: str = models.Field(..., description="your name")
    text: str = models.Field(..., description="what are you want to say?")


class HTTP(View):
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

## 绑定响应

为了描述不同状态码的响应结果，Index 使用装饰器描述，而不是类型注解。

!!! notice
    此功能到目前为止，除生成OpenAPI文档的作用外，无其他作用。

```python
from index.view import View
from index.test import TestView
from index.responses import TemplateResponse
from index.openapi import models, describe


class Hello(models.Model):
    name: str = models.Field("Aber", description="your name")


class Message(models.Model):
    """your message"""

    name: str = models.Field(..., description="your name")
    text: str = models.Field(..., description="what are you want to say?")


class MessageResponse(models.Model):
    """message response"""

    message: Message


class HTTP(View):
    async def get(self, query: Hello):
        """
        welcome page
        """
        return TemplateResponse(
            "home.html",
            {"request": self.request, "name": query.name},
        )

    @describe(200, MessageResponse)
    @describe(201, None)
    async def post(self, body: Message):
        """
        echo your message

        just echo your message.
        """
        return {"message": body.dict()}, 200, {"server": "index.py"}
```
