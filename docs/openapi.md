Index 使用 [pydantic](https://pydantic-docs.helpmanual.io/) 用于更轻松的解析 HTTP 请求信息，并为之绑定了一套生成 OpenAPI 文档的程序。

## 显示 OpenAPI 文档

将 `indexpy.openapi.application.OpenAPI` 挂载进 index 中。启动 index，访问你服务上 `/openapi/` 即可看到生成的文档。

```python
from indexpy import Index
from indexpy.routing import SubRoutes
from indexpy.openapi import OpenAPI

app = Index()

app.router.extend(
    SubRoutes(
        "/openapi",
        OpenAPI("Title", "description", "1.0").routes,
        namespace="openapi",
    )
)
```

默认的文档模板使用 [swagger](https://swagger.io/tools/swagger-ui/)，如果你更喜欢 [redoc](https://github.com/Redocly/redoc) 的样式，可以通过更改 `template_name` 来达到目的，例如：`OpenAPI(..., template_name="redoc")`。

不仅如此，你还可以通过使用 `template` 参数来控制显示自己的喜欢的任何模板，只需要把模板的完整内容作为字符串传给 `template` 参数即可。

## 接口描述

对于所有可处理 HTTP 请求的方法，它们的 `__doc__` 都会用于生成 OpenAPI 文档。

第一行将被当作概要描述，所以尽量简明扼要，不要太长。

空一行之后，后续的文字都会被当作详细介绍，被安置在 OpenAPI 文档中。

例如：

```python
async def handler(request):
    """
    api summary

    api description..........................
    .........................................
    .........................................
    """
```

### 描述请求参数

对于所有可处理 HTTP 请求的方法，均可以接受五种参数：`Path`、`Body`、`Query`、`Header`、`Cookie`。对参数进行类型标注，就做到自动参数校验以及生成请求格式文档。例如：

```python
from indexpy.http import Query


async def getlist(
    request,
    page_num: int = Query(...),
    page_size: int = Query(...)
):
    ...
```

而你也可以通过使用继承自 `pydantic.BaseModel` 的类作为类型注解来描述同一类型的全部参数，通过类的继承可以做到复用参数。`Exclusive` 接受五种请求参数的全小写字符串作为参数，分别代表对应五种请求参数的独占模式。下例与上例是等价的。

```python
from pydantic import BaseModel
from indexpy.http import Exclusive


class PageQuery(BaseModel):
    page_num: int
    page_size: int


async def getlist(request, query: PageQuery = Exclusive("query")):
    ...
```

### 描述响应结果

为了描述不同状态码的响应结果，Index 使用装饰器描述，而不是类型注解。`describe_response` 接受五个参数，其中 `status` 为必需项，`description`、`content`、`headers` 和 `links` 为可选项，对应[ OpenAPI Specification ](https://github.com/OAI/OpenAPI-Specification/blob/master/versions/3.0.0.md#responseObject)里的同名字段。

其中，`content` 既可以使用类型对象或 `pydantic.BaseModel` 的派生子类描述响应，亦可以直接传递符合 OpenAPI 文档的 Dict（当你描述返回一个非 application/json 类型的响应时这很有用）。

!!! notice

    如果 `description` 的值为默认的 `""`，则会使用 `http` 标准库中的 `HTTPStatus(status).description` 作为描述。

```python
from http import HTTPStatus

from indexpy.openapi import describe_response


@describe_response(HTTPStatus.NO_CONTENT)
def handler(request):
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
def handler(request):
    """
    .................
    """
```

!!! notice
    此功能到目前为止，除生成OpenAPI文档的作用外，无其他作用。**未来或许会增加 mock 功能。**

## 描述额外的 OpenAPI 文档

作为一个 Web 项目，在中间件中读取请求信息并作限制是很常见的，例如读取 JWT 用作鉴权。在每个视图都增加 `header` 参数是不现实的，这时候 `describe_extra_docs` 就派上用场了。

!!! tip

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

## Tags

OpenAPI 的 Tags 是一个有用的功能，在 Index 里，你可以通过如下方式来指定 URL 的分类标签。

`tags` 参数必须是一个 `dict` 类型，键为标签名。值需要包含 `description`，用于描述此标签；`paths` 是 URL 列表，如果 URL 包含路径参数，直接使用不带 `:type` 的字符串即可。

```python
OpenAPI(
    "index.py example",
    "just a example, power by index.py",
    "v1",
    tags={
        "something": {
            "description": "test over two tags in one path",
            "paths": ["/about/", "/file", "/"],
        },
        "about": {
            "description": "about page",
            "paths": ["/about/", "/about/me"],
        },
        "file": {
            "description": "get/upload file api",
            "paths": ["/file"],
        },
    },
)
```
