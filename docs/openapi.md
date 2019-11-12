Index 内置了一套解析请求的模型，并为之绑定了一套生成 OpenAPI 文档的程序。

**到目前为止，此功能仍然是实验性的。**

## 显示文档

*如果你不想要查看生成的文档，那么这一步不是必须的。*

在 `mounts.py` 中写入如下内容，可将 `index.openapi.application.OpenAPI` 挂载进 index 中。

```python
from index import app
from index.openapi.application import OpenAPI

app.mount(
    "/openapi",
    OpenAPI("index.py example", "just a example, power by index.py", "0.1.0"),
)
```

启动 index，访问你服务上 `/openapi/` 即可看到生成的文档。

## 解析请求

一般来说，index 的视图函数只需要处理两种请求参数——query 和 request body。

如下例所示，只需要在视图函数中增加对应名称的参数即可。

```python
from index.view import View
from index.openapi import models


class Hello(models.Model):
    name = models.StrField(description="name")


class Message(models.Model):
    """your message"""

    name = models.StrField(description="your name")
    text = models.StrField(description="what are you want to say?")


class HTTP(View):
    async def get(self, query: Hello):
        """
        welcome page
        """
        return f"hello {query.name}"

    async def post(self, body: Message):
        """
        echo your message

        just echo your message
        """
        return {"message": body.data}, 200, {"server": "index.py"}
```

## 绑定响应

为了描述不同状态码的响应结果，Index 使用装饰器描述，而不是注解。

```python
from index.view import View
from index.openapi import models, bindresponse


class Message(models.Model):
    """your message"""

    name = models.StrField(description="your name")
    text = models.StrField(description="what are you want to say?")


class MessageResponse(models.Model):
    """message response"""

    message = models.ModelField(Message)


class HTTP(View):

    @bindresponse(200, MessageResponse)
    async def post(self, body: Message):
        """
        echo your message

        just echo your message.
        """
        return {"message": body.data}, 200, {"server": "index.py"}
```
