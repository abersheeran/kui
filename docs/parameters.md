Index-py 使用 [pydantic](https://pydantic-docs.helpmanual.io/) 用于更轻松的解析 HTTP 请求信息，并为之绑定了一套生成 OpenAPI 文档的程序。

## 显示 OpenAPI 文档

将 `indexpy.openapi.application.OpenAPI` 挂载进 Index-py 中。启动 index，访问你服务上 `/docs/` 即可看到生成的文档。

!!! tip ""
    如果你不需要生成文档，仅仅只需要自动校验参数功能，这一步可以跳过。

```python
from indexpy import Index
from indexpy.openapi import OpenAPI

app = Index()

app.router << ("/docs" // OpenAPI().routes)
```

默认的文档模板使用 [swagger](https://swagger.io/tools/swagger-ui/)，如果你更喜欢 [redoc](https://github.com/Redocly/redoc) 或 [rapidoc](https://mrin9.github.io/RapiDoc/) 的样式，可以通过更改 `template_name` 来达到目的，例如：`OpenAPI(..., template_name="redoc")`。

不仅如此，你还可以通过使用 `template` 参数来控制显示自己的喜欢的任何模板，只需要把模板的完整内容作为字符串传给 `template` 参数即可。

### API Tags

OpenAPI 的 Tags 是一个有用的功能，在 Index-py 里，你可以通过如下方式来指定 URL 的分类标签。

`tags` 参数必须是一个 `dict` 类型，键为标签名。值需要包含 `description`，用于描述此标签；`paths` 是 URL 列表，如果 URL 包含路径参数，直接使用不带 `:type` 的字符串即可。

```python
OpenAPI(
    ......,
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

你也可以在使用[装饰器注册](./route.md)时，给装饰器传入 `tags` 参数，如下。虽然这种方式没办法为 `tag` 增加 `description`，但它可以与上述用法同时使用——换句话来说，你可以在 `OpenAPI` 的 `tags` 里定义 `tag` 的信息，再在装饰器里传入对应的 `tag` 名称。

```python
from indexpy import Routes

routes = Routes()


@routes.http('/', tags=["tag0", "tag1"])
async def handler():
    return "/"
```

## 接口描述

对于所有可处理 HTTP 请求的方法，它们的 `__doc__` 都会用于生成 OpenAPI 文档。第一行将被当作概要描述，所以尽量简明扼要，不要太长。空一行之后，后续的文字都会被当作详细介绍，被安置在 OpenAPI 文档中。

例如：

```python
from indexpy import HTTPView


async def handler():
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

你也可以在使用[装饰器注册](./route.md)时，给装饰器传入参数，如下。

```python
from indexpy import Routes

routes = Routes()


@routes.http('/', summary="api summary", description="api description.............")
async def handler():
    return "/"
```

如果你的 description 很长，也可以只给装饰器传入 `summary` 参数，`description` 将自动使用整个 `__doc__`。

```python
from indexpy import Routes

routes = Routes()


@routes.http('/', summary="api summary")
async def handler():
    """
    api description..........................
    .........................................
    .........................................
    """
    return "/"
```

## 标注请求参数

先看一个最简单的例子，两个分页参数，首先通过 Type hint 标注它们都需要 `int` 类型，在给予它们 `Query(...)` 作为额外的类型描述。

`Query` 代表它们将会从 `request.query_params` 中读取值，`...` 作为第一个参数，意味着它没有默认值，也就是客户端请求该接口时必须传递值。譬如：`?page_num=1&page_size=10`。

如果你使用 `Query(10)` 则意味着这个值可以不由前端传递，其默认值为 `10`。

```python
from typing_extensions import Annotated
from indexpy import Query


async def getlist(
    page_num: Annotated[int, Query(...)],
    page_size: Annotated[int, Query(...)],
):
    ...
```

也可以通过使用继承自 `pydantic.BaseModel` 的类作为类型注解来描述同一类型的全部参数，下例与上例是等价的。

```python
from typing_extensions import Annotated
from indexpy import Query
from pydantic import BaseModel


class PageQuery(BaseModel):
    page_num: int
    page_size: int


async def getlist(query: Annotated[PageQuery, Query(exclusive=True)]):
    ...
```

同样的，你还可以使用其他对象来获取对应部分的参数，以下是对照：

- `Path`：`request.path_params`
- `Query`：`request.query_params`
- `Header`：`request.headers`
- `Cookie`：`request.cookies`
- `Body`：`await request.data()`

通过这样标注的请求参数，不仅会自动校验、转换类型，还能自动生成接口文档。在你需要接口文档的情况下，十分推荐这么使用。

!!! tip ""

    路径参数（`Path`）的校验错误是比较特别的，它会尝试调用用户自己注册的 404 异常处理方法或者默认的 404 异常处理方法返回 404 状态，就像没有找到路由一样，而不是像其他参数校验错误一样返回 422 状态。

### 依赖可调用对象

使用 `Depends(func)` 可以标注所依赖的可调用对象，在视图被调用前会调用并将返回值注入到视图的参数中。

!!! tip ""

    你同样可以在这里进行参数标注，将会递归调用所有依赖的可调用对象以及需要注入的参数。

```python
def get_name(name: Annotated[str, Query(...)]):
    return name.lower()


async def hello(name: Annotated[str, Depends(get_name)]):
    return f"hello {name}"
```

比较特殊的是，如果你使用 `Depends(......)` 标注的可调用对象是一个生成器函数，那么它将会被 [`contextlib`](https://docs.python.org/3/library/contextlib.html) 改造，`yield` 值被注入视图中，清理部分在视图函数退出后执行（无论视图函数是正常返回或是抛出异常，均会执行清理过程）。在获取某些需要清理的资源时，这特别有效。

```python
async def get_db_connection():
    connection = ...  # get connection
    try:
        yield connection
    finally:
        connection.close()


async def get_user(db: Annotated[Connection, Depends(get_db_connection)]):
    ...
```

### 修改 Content-Type

Index-py 会自动读取 `request.data` 的函数签名，并读取其中包含的 `ContentType` 对象作为 Content-Type 生成 OpenAPI 文档。以下为一个简单自定义样例——使用 `msgpack` 解析数据：

```python
import typing
from http import HTTPStatus

import msgpack
from typing_extensions import Annotated

from indexpy import Index
from indexpy.applications import FactoryClass
from indexpy.requests import HttpRequest


class MsgPackRequest(HttpRequest):
    async def data(self) -> Annotated[typing.Any, ContentType("application/x-msgpack")]:
        if self.content_type == "application/x-msgpack":
            return msgpack.unpackb(await self.body)

        raise HTTPException(
            HTTPStatus.UNSUPPORTED_MEDIA_TYPE,
            headers={"Accept": "application/x-msgpack"},
        )


app = Index(factory_class=FactoryClass(http=MsgPackRequest))
```

### 读取 `request` 属性

或许有时候你需要直接读取 `request` 的某些属性，以配合中间件使用。但直接使用 `request.attr` 又失去了 Type hint 的好处，那么可以选择使用如下方式。

如下例所示，当 `code` 被调用时会自动读取 `request.user` 并作为函数参数传入函数中。

```python
from typing_extensions import Annotated
from indexpy import Request
from yourmodule import User


async def code(user: Annotated[User, Request()]):
    ...
```

当需要读取的属性名称不能作为参数名称时，也可以为 `Request` 传入一个字符串作为属性名进行读取。如下例所示，`request.user.name` 将会作为函数参数 `username` 传入函数中。

```python
from typing_extensions import Annotated
from indexpy import Request


async def code(username: Annotated[str, Request(alias="user.name")]):
    ...
```

### 在中间件中使用

在中间件中的使用方式并没有什么不同，直接在参数里描述即可。

```python
from typing_extensions import Annotated


def required_auth(endpoint):
    async def wrapper(authorization: Annotated[str, Header()]):
        ...
        return await endpoint()

    return wrapper
```

## 描述响应结果

为了生成响应结果的 OpenAPI 文档，你应当使用 [`Annotated`](https://docs.python.org/zh-cn/3/library/typing.html#typing.Annotated) 对视图的返回值进行描述。

```python
from typing_extensions import Annotated
from indexpy import Index, JSONResponse

app = Index()


@app.router.http.get("/hello")
async def hello() -> Annotated[Any, JSONResponse[200, {}, List[str]]]:
    """
    hello
    """
    return ["hello", "world"]
```

你还可以描述多个响应结果，如下所示：

```python
from typing_extensions import Annotated
from indexpy import Index, JSONResponse

app = Index()


class ErrorMessage(BaseModel):
    code: int
    message: str


@app.router.http.get("/hello")
async def hello() -> Annotated[
    Any,
    JSONResponse[200, {}, List[str]],
    JSONResponse[400, {}, ErrorMessage]
]:
    """
    hello
    """
    ...
```

使用不同的 Response 子类可以生成不同的响应结果文档。

!!! tip "缺省"
    只有第一个参数是必须的，其他参数都可不填。

所有响应里的 `headers` 参数应当是一个标准的 [OpenAPI Response](https://github.com/OAI/OpenAPI-Specification/blob/main/versions/3.0.3.md#responseObject) 中所需要的 Headers 字典。例如：`{"Location": {"schema": {"type": "string"}}}`。

- json: `JSONResponse[status_code, headers, content]`
    - `content`: 可以是标准 [OpenAPI Response](https://github.com/OAI/OpenAPI-Specification/blob/main/versions/3.0.3.md#responseObject) 中所需要的 Content 字典；也可以是 `TypedDict`、`str` 之类的类型，还可以是 `pydantic.BaseModel` 的子类。

- html: `HTMLResponse[status_code, headers]`
- text: `TextResponse[status_code, headers]`
- redirect: `RedirectResponse[status_code, headers]`
- file: `FileResponse[content_type, headers]`
    - `content_type`: 指定返回的文件的 Content-Type。

除此之外，你还可以直接使用标准 [OpenAPI Response](https://github.com/OAI/OpenAPI-Specification/blob/main/versions/3.0.3.md#responseObject) 字典（`dict`）来描述响应结果，这同样会被解析、插入到最终生成的 API 文档里。

### 在中间件中使用

在中间件中的使用方式并没有什么不同。

```python
from typing_extensions import Annotated


def required_auth(endpoint):
    async def wrapper(authorization: Annotated[str, Header()]) -> Annotated[Any, HttpResponse[401]]:
        ...
        return await endpoint()

    return wrapper
```

## 描述额外的 OpenAPI 文档

可以使用 `describe_extra_docs` 对接口所对应的 OpenAPI 文档描述进行补充，使用 `describe_extra_docs` 增加的任何描述都会被合并进原本的文档里。

!!! tip ""
    具体的字段可参考 [OpenAPI Specification](https://github.com/OAI/OpenAPI-Specification/blob/master/versions/3.0.0.md#operationObject)。

例如你可以使用它来描述 Indexpy 并不自带的 `security`：

```python
from typing_extensions import Annotated


def required_auth(endpoint):
    describe_extra_docs(endpoint, {"security": [{"BearerAuth": []}]})

    async def wrapper(authorization: Annotated[str, Header()]) -> Annotated[Any, HttpResponse[401]]:
        ...
        return await endpoint()

    return wrapper
```
