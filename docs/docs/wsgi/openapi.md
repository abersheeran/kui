编写如下代码，访问你服务上 `/docs/` 即可看到生成的文档。

```python
from kui.wsgi import Kui, OpenAPI

app = Kui()

app.router << ("/docs" // OpenAPI().routes)
```

默认的文档模板使用 [swagger](https://swagger.io/tools/swagger-ui/)，如果你更喜欢 [redoc](https://github.com/Redocly/redoc) 或 [rapidoc](https://mrin9.github.io/RapiDoc/) 的样式，可以通过更改 `template_name` 来达到目的，例如：`OpenAPI(..., template_name="redoc")`。

不仅如此，你还可以通过使用 `template` 参数来控制显示自己的喜欢的任何模板，只需要把模板的完整内容作为字符串传给 `template` 参数即可。

### 标签

在 Kuí 里，你可以通过如下方式来定义 Tag 的 `description` 值。

```python
OpenAPI(
    ......,
    tags={
        "tag-name": {
            "description": ".......",
        },
    },
)
```

!!! tip
    如果不需要为 `tag` 增加 `description`，那么可以跳过这一步。

在注册路由时传入 `tags` 参数，

```python
from kui.wsgi import Routes

routes = Routes()


@routes.http.get('/', tags=["tag-name", "tag-name-2"])
def handler():
    return "/"
```

## 接口介绍

对于所有可处理 HTTP 请求的方法，它们的 `__doc__` 都会用于生成 OpenAPI 文档。第一行将被当作概要描述，所以尽量简明扼要，不要太长。空一行之后，后续的文字都会被当作详细介绍，被安置在 OpenAPI 文档中。

例如：

```python
from kui.wsgi import HTTPView


def handler():
    """
    api summary

    api description..........................
    .........................................
    .........................................
    """


class ClassHandler(HTTPView):
    def get(self):
        """
        api summary

        api description..........................
        .........................................
        .........................................
        """
```

你也可以在注册路由传入参数。

```python
from kui.wsgi import Routes

routes = Routes()


@routes.http.get('/', summary="api summary", description="api description.............")
def handler():
    return "/"
```

如果你的 description 很长，也可以只给装饰器传入 `summary` 参数，`description` 将自动使用整个 `__doc__`。

```python
from kui.wsgi import Routes

routes = Routes()


@routes.http.get('/', summary="api summary")
def handler():
    """
    api description..........................
    .........................................
    .........................................
    """
    return "/"
```

## 描述请求参数

当你使用[依赖注入](./dependency-injection.md)时，请求参数将自动生成。

### 修改 Content-Type

Kuí 会自动读取 `app.factory_class.http.data` 的函数签名，并读取其中包含的 `ContentType` 对象作为 Content-Type 生成 OpenAPI 文档。

一个简单自定义样例——使用 `msgpack` 解析数据：

```python
import typing
from http import HTTPStatus

import msgpack
from typing_extensions import Annotated

from kui.wsgi import Kui, FactoryClass, HttpRequest


class MsgPackRequest(HttpRequest):
    def data(self) -> Annotated[typing.Any, ContentType("application/x-msgpack")]:
        if self.content_type == "application/x-msgpack":
            return msgpack.unpackb(self.body)

        raise HTTPException(
            HTTPStatus.UNSUPPORTED_MEDIA_TYPE,
            headers={"Accept": "application/x-msgpack"},
        )


app = Index(factory_class=FactoryClass(http=MsgPackRequest))
```

## 描述响应结果

为了生成响应结果的 OpenAPI 文档，你应当使用 [`Annotated`](https://docs.python.org/zh-cn/3/library/typing.html#typing.Annotated) 对视图的返回值进行描述。

```python
from typing_extensions import Annotated
from kui.wsgi import Kui, JSONResponse

app = Kui()


@app.router.http.get("/hello")
def hello() -> Annotated[Any, JSONResponse[200, {}, List[str]]]:
    """
    hello
    """
    return ["hello", "world"]
```

你还可以描述多个响应结果，如下所示：

```python
from typing_extensions import Annotated
from kui.wsgi import Kui, JSONResponse
from pydantic import BaseModel

app = Kui()


class ErrorMessage(BaseModel):
    code: int
    message: str


@app.router.http.get("/hello")
def hello() -> Annotated[
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

### 在中间件里使用

在中间件里的使用方式并没有什么不同。

```python
from typing_extensions import Annotated


def required_auth(endpoint):
    def wrapper(authorization: Annotated[str, Header()]) -> Annotated[Any, HttpResponse[401]]:
        ...
        return await endpoint()

    return wrapper
```

### 在依赖函数里使用

在依赖函数里的使用方式并没有什么不同。

```python
from typing_extensions import Annotated


def required_auth(authorization: Annotated[str, Header()]) -> Annotated[Any, HttpResponse[401]]:
    ...
```

## 描述额外的 OpenAPI 文档

可以使用 `describe_extra_docs` 对接口所对应的 OpenAPI 文档描述进行补充，使用 `describe_extra_docs` 增加的任何描述都会被合并进原本的文档里。

!!! tip ""
    具体的字段可参考 [OpenAPI Specification](https://github.com/OAI/OpenAPI-Specification/blob/master/versions/3.0.0.md#operationObject)。

例如你可以使用它来描述 Kuí 并不自带的 `security`：

```python
from typing_extensions import Annotated
from kui.wsgi import Kui, OpenAPI

app = Kui()

openapi = OpenAPI(
    security_schemes={"BearerAuth": {"type": "http", "scheme": "bearer"}},
)
app.router << ("/docs" // openapi.routes)


def required_auth(endpoint):
    describe_extra_docs(endpoint, {"security": [{"BearerAuth": []}]})

    def wrapper(authorization: Annotated[str, Header()]) -> Annotated[Any, HttpResponse[401]]:
        ...
        return await endpoint()

    return wrapper
```
