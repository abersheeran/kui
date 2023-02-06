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

通过这样标注的请求参数，不仅会自动校验、转换类型，还能自动生成接口文档。在你需要接口文档的情况下，十分推荐这么使用。

!!! tip

    路径参数（`Path`）的校验错误是比较特别的，它会尝试调用用户自己注册的 404 异常处理方法或者默认的 404 异常处理方法返回 404 状态，就像没有找到路由一样，而不是像其他参数校验错误一样返回 422 状态。

## 依赖可调用对象

使用 `Depends(func)` 可以标注所依赖的可调用对象，在视图被调用前会调用并将返回值注入到视图的参数中。

!!! tip

    你同样可以在这里进行参数标注，将会递归调用所有依赖的可调用对象以及需要注入的参数。

```python
def get_name(name: Annotated[str, Query(...)]):
    return name.lower()


def hello(name: Annotated[str, Depends(get_name)]):
    return f"hello {name}"
```

比较特殊的是，如果你使用 `Depends(......)` 标注的可调用对象是一个生成器函数，那么它将会被 [`contextlib`](https://docs.python.org/3/library/contextlib.html) 改造，`yield` 值被注入视图中，清理部分在视图函数退出后执行（无论视图函数是正常返回或是抛出异常，均会执行清理过程）。在获取某些需要清理的资源时，这特别有效。

```python
def get_db_connection():
    connection = ...  # get connection
    try:
        yield connection
    finally:
        connection.close()


def get_user(db: Annotated[Connection, Depends(get_db_connection)]):
    ...
```

## 读取 `request` 属性

或许有时候你需要直接读取 `request` 的某些属性，以配合中间件使用。但直接使用 `request.attr` 又失去了 Type hint 的好处，那么可以选择使用如下方式。

如下例所示，当 `code` 被调用时会自动读取 `request.user` 并作为函数参数传入函数中。

```python
from typing_extensions import Annotated
from kui.wsgi import RequestAttr
from yourmodule import User


def code(user: Annotated[User, RequestAttr()]):
    ...
```

当需要读取的属性名称不能作为参数名称时，也可以为 `RequestAttr` 传入一个字符串作为属性名进行读取。如下例所示，`request.user.name` 将会作为函数参数 `username` 传入函数中。

```python
from typing_extensions import Annotated
from kui.wsgi import RequestAttr


def code(username: Annotated[str, RequestAttr(alias="user.name")]):
    ...
```

## 在中间件中使用

在中间件中的使用方式并没有什么不同，直接在参数里描述即可。

```python
from typing_extensions import Annotated


def required_auth(endpoint):
    def wrapper(authorization: Annotated[str, Header()]):
        ...
        return endpoint()

    return wrapper
```
