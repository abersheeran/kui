先看一个最简单的例子，两个分页参数，首先通过 Type hint 标注它们都需要 `int` 类型，在给予它们 `Query(...)` 作为额外的类型描述。

`Query` 代表它们将会从 `request.query_params` 中读取值，`...` 作为第一个参数，意味着它没有默认值，也就是客户端请求该接口时必须传递值。譬如：`?page_num=1&page_size=10`。

如果你使用 `Query(10)` 则意味着这个值可以不由前端传递，其默认值为 `10`。

```python
from typing_extensions import Annotated
from kui.wsgi import Query


def getlist(
    page_num: Annotated[int, Query(...)],
    page_size: Annotated[int, Query(...)],
):
    ...
```

也可以通过使用继承自 `pydantic.BaseModel` 的类作为类型注解来描述同一类型的全部参数，下例与上例是等价的。

```python
from typing_extensions import Annotated
from kui.wsgi import Query
from pydantic import BaseModel


class PageQuery(BaseModel):
    page_num: int
    page_size: int


def getlist(query: Annotated[PageQuery, Query(exclusive=True)]):
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

!!! tip "在中间件中使用"

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
