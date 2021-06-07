Index-py 使用 [pydantic](https://pydantic-docs.helpmanual.io/) 用于更轻松的解析 HTTP 请求信息，并为之绑定了一套生成 OpenAPI 文档的程序。

## 显示 OpenAPI 文档

将 `indexpy.openapi.application.OpenAPI` 挂载进 Index-py 中。启动 index，访问你服务上 `/openapi/` 即可看到生成的文档。

!!! tip ""
    如果你不需要生成文档，仅仅只需要自动校验参数功能，这一步可以跳过。

```python
from indexpy import Index
from indexpy.openapi import OpenAPI

app = Index()

app.router << ("/openapi" // OpenAPI("Title", "description", "1.0").routes)
```

默认的文档模板使用 [swagger](https://swagger.io/tools/swagger-ui/)，如果你更喜欢 [redoc](https://github.com/Redocly/redoc) 或 [rapidoc](https://mrin9.github.io/RapiDoc/) 的样式，可以通过更改 `template_name` 来达到目的，例如：`OpenAPI(..., template_name="redoc")`。

不仅如此，你还可以通过使用 `template` 参数来控制显示自己的喜欢的任何模板，只需要把模板的完整内容作为字符串传给 `template` 参数即可。

### API Tags

OpenAPI 的 Tags 是一个有用的功能，在 Index-py 里，你可以通过如下方式来指定 URL 的分类标签。

`tags` 参数必须是一个 `dict` 类型，键为标签名。值需要包含 `description`，用于描述此标签；`paths` 是 URL 列表，如果 URL 包含路径参数，直接使用不带 `:type` 的字符串即可。

```python
OpenAPI(
    title="index.py example",
    description="just a example, power by index.py",
    version="v1",
    tags={
        "something": {
            "description": "test over two tags in one path",
            "paths": ["/about/{username}", "/file", "/"],
        },
        "about": {
            "description": "about page",
            "paths": ["/about/", "/about/{username}"],
        },
    },
)
```

## 接口描述

对于所有可处理 HTTP 请求的方法，它们的 `__doc__` 都会用于生成 OpenAPI 文档。第一行将被当作概要描述，所以尽量简明扼要，不要太长。空一行之后，后续的文字都会被当作详细介绍，被安置在 OpenAPI 文档中。

例如：

```python
from indexpy import HTTPView


async def handler(request):
    """
    api summary

    api description..........................
    .........................................
    .........................................
    """


class ClassHandler(HTTPView):
    async def get(self):
        """
        api summary

        api description..........................
        .........................................
        .........................................
        """
```

## 标注请求参数

先看一个最简单的例子，两个分页参数，首先通过 Type hint 标注它们都需要 `int` 类型，在给予它们 `Query(...)` 作为值，`Query` 代表它们将会从 `request.query_params` 中读取值，`...` 作为第一个参数，意味着它没有默认值，也就是客户端请求该接口时必须传递值。譬如：`?page_num=1&page_size=10`。如果你使用 `Query(10)` 则意味着这个值可以不由前端传递，其默认值为 `10`。

```python
from indexpy import Query


async def getlist(
    request,
    page_num: int = Query(...),
    page_size: int = Query(...)
):
    ...
```

也可以通过使用继承自 `pydantic.BaseModel` 的类作为类型注解来描述同一类型的全部参数，通过类的继承可以做到复用参数。下例与上例是等价的。

```python
from indexpy import Query
from pydantic import BaseModel


class PageQuery(BaseModel):
    page_num: int
    page_size: int


async def getlist(query: PageQuery = Query(exclusive=True)):
    ...
```

同样的，你还可以使用其他对象来获取对应部分的参数，以下是对照：

- `Path`：`request.path_params`
- `Query`：`request.query_params`
- `Header`：`request.headers`
- `Cookie`：`request.cookies`
- `Body`：`await request.data()`

通过这样标注的请求参数，不仅会自动校验、转换类型，还能自动生成接口文档。在你需要接口文档的情况下，十分推荐这么使用。

---

或许有时候你需要直接读取 `request` 的某些属性，以配合中间件使用。

如下例所示，当 `code` 被调用时会自动读取 `request.user` 并作为函数参数传入函数中。

```python
from indexpy import Request
from yourmodule import User


async def code(user: User = Request()):
    ...
```

当需要读取的属性名称不能作为参数名称时，也可以为 `Request` 传入一个字符串作为属性名进行读取。如下例所示，`request.user.name` 将会作为函数参数 `username` 传入函数中。

```python
from indexpy import Request


async def code(username: str = Request(alias="user.name")):
    ...
```

## 描述响应结果

为了描述不同状态码的响应结果，Index-py 使用装饰器描述，而不是类型注解。`describe_response` 接受五个参数，其中 `status` 为必需项，`description`、`content`、`headers` 和 `links` 为可选项，对应[ OpenAPI Specification ](https://github.com/OAI/OpenAPI-Specification/blob/master/versions/3.0.0.md#responseObject)里的同名字段。

其中，`content` 既可以使用类型对象或 `pydantic.BaseModel` 的派生子类描述响应，亦可以直接传递符合 OpenAPI 文档的 Dict（当你描述返回一个非 application/json 类型的响应时这很有用）。

!!! notice ""
    如果 `description` 的值为默认的 `""`，则会使用 `http` 标准库中的 `HTTPStatus(status).description` 作为描述。

```python
from http import HTTPStatus

from indexpy.openapi import describe_response


@describe_response(HTTPStatus.NO_CONTENT)
def handler():
    """
    .................
    """
```

除了 `describe_response` 描述单个响应状态码以外，你还可以使用 `describe_responses` 对状态码批量的描述。字典以 `status` 为键，以 OpenAPI Response Object 的四个属性作为可选的值（其中 `description` 为必选）。

```python
from indexpy.openapi import describe_responses

RESPONSES = {
    404: {"description": "Item not found"},
    403: {"description": "Not enough privileges"},
    302: {"description": "The item was moved"},
}


@describe_responses(RESPONSES)
@describe_response(204, "No Content")
def handler():
    """
    .................
    """
```

!!! notice ""
    此功能到目前为止，除生成OpenAPI文档的作用外，无其他作用。**未来或许会增加 mock 功能。**

## 描述额外的 OpenAPI 文档

作为一个 Web 项目，在中间件中读取请求信息并作限制是很常见的，例如读取 JWT 用作鉴权。在每个视图都增加 `header` 参数是不现实的，这时候 `describe_extra_docs` 就派上用场了。

!!! tip ""
    `describe_extra_docs` 增加的内容，不仅限于 `parameters`，任何描述都会被合并进原本的文档里。具体的字段可参考 [OpenAPI Specification](https://github.com/OAI/OpenAPI-Specification/blob/master/versions/3.0.0.md#operationObject)。

```python
def judge_jwt(endpoint):
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

    async def judge(request):
        ...

    return judge
```
