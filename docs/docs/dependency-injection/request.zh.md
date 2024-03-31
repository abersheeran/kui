你可以使用类型标注来获取请求的参数，Kuí 会自动校验参数并返回错误信息。以下是一个简单、常见的分页参数例子：

```python
from typing_extensions import Annotated
from kui.wsgi import Query


def getlist(
    page_num: Annotated[int, Query(...)],
    page_size: Annotated[int, Query(...)],
):
    ...
```

有时候前端可能要求传入的参数使用小驼峰命名法，而 PEP8 推荐 Python 程序使用下划线命名法，这时候你可以使用 `alias` 参数来指定参数名。

```python
from typing_extensions import Annotated
from kui.wsgi import Query


def getlist(
    page_num: Annotated[int, Query(..., alias="pageNum")],
    page_size: Annotated[int, Query(..., alias="pageSize")],
):
    ...
```

你还可以指定参数的默认值，这样当前端没有给出对应参数时会使用默认值。

```python

from typing_extensions import Annotated
from kui.wsgi import Query


def getlist(
    page_num: Annotated[int, Query(1)],
    page_size: Annotated[int, Query(10)],
):
    ...
```

生成文档时，你可能会想告诉使用这个 API 的人关于参数的一些信息，这时你可以使用 `title` 和 `description` 参数。

```python
from typing_extensions import Annotated
from kui.wsgi import Query


def getlist(
    page_num: Annotated[int, Query(..., title="Page Num", description="页码")],
    page_size: Annotated[int, Query(..., title="Page Size", description="每页数量")],
):
    ...
```

同样的，你还可以使用其他对象来获取对应部分的参数，以下是对照：

- `Path`：`request.path_params`
- `Query`：`request.query_params`
- `Header`：`request.headers`
- `Cookie`：`request.cookies`
- `Body`：`request.data()`

!!! tip "Path 参数校验失败"

    路径参数（`Path`）的校验错误是比较特别的，它会尝试调用用户自己注册的 404 异常处理方法或者默认的 404 异常处理方法返回 404 状态，就像没有找到路由一样，而不是像其他参数校验错误一样返回 422 状态。

!!! tip "使用一个 Model 解析请求体"

    有时候你可能会想要使用一个 Model 来解析请求体，这时你可以指定 `Body(..., exclusive=True)`。

    ```python
    from typing_extensions import Annotated
    from pydantic import BaseModel
    from kui.wsgi import Body


    class User(BaseModel):
        username: str
        password: str


    def login(user: Annotated[User, Body(..., exclusive=True)]):
        ...
    ```

## 在中间件中使用

在中间件中使用参数校验没有什么不同。

```python
from typing_extensions import Annotated


def required_auth(endpoint):
    def wrapper(authorization: Annotated[str, Header()]):
        ...
        return endpoint()

    return wrapper
```

## 文件上传

Kuí 提供了 `UploadFile` 类，用于描述文件上传的参数。

```python
from kui.wsgi import Kui, UploadFile, Body

app = Kui()


@app.router.http.post("/")
def upload_file(file: Annotated[UploadFile, Body(...)]):
    return {
        "filename": file.filename,
        "content": file.read().decode("utf8"),
    }
```

!!! tip "OpenAPI 文档"
    这同样也会自动生成 OpenAPI 文档 `{"type": "string", "format": "binary"}`。
