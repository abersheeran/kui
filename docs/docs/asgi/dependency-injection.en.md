Let's start with a simple example, with two pagination parameters. First, annotate them with the `int` type using Type hints, and provide `Query(...)` as an additional type description.

`Query` indicates that they will be read from `request.query_params`. The `...` as the first argument means that it doesn't have a default value, so the client must pass a value when requesting this API. For example: `?page_num=1&page_size=10`.

If you use `Query(10)`, it means that this value can be omitted by the frontend, and its default value is `10`.

```python
from typing_extensions import Annotated
from kui.asgi import Query


async def getlist(
    page_num: Annotated[int, Query(...)],
    page_size: Annotated[int, Query(...)],
):
    ...
```

You can also use a class that inherits from `pydantic.BaseModel` as a type annotation to describe all parameters of the same type. The following example is equivalent to the previous one.

```python
from typing_extensions import Annotated
from kui.asgi import Query
from pydantic import BaseModel


class PageQuery(BaseModel):
    page_num: int
    page_size: int


async def getlist(query: Annotated[PageQuery, Query(exclusive=True)]):
    ...
```

Similarly, you can use other objects to retrieve corresponding parts of the parameters. Here is a comparison:

- `Path`: `request.path_params`
- `Query`: `request.query_params`
- `Header`: `request.headers`
- `Cookie`: `request.cookies`
- `Body`: `await request.data()`

By annotating the request parameters in this way, not only will they be automatically validated and type-converted, but they can also generate API documentation automatically. It is highly recommended to use it when you need API documentation.

!!! tip

    Validation errors for path parameters (`Path`) are handled in a special way. It will attempt to call the user-registered 404 exception handler or the default 404 exception handler to return a 404 status, as if the route was not found, instead of returning a 422 status like other parameter validation errors.

## Dependency Callable Objects

You can use `Depends(func)` to annotate the callable objects that the view depends on. The return value will be injected into the view's parameters before the view is called.

!!! tip

    You can also annotate the parameters here, and all dependent callable objects and the parameters to be injected will be recursively called.

```python
def get_name(name: Annotated[str, Query(...)]):
    return name.lower()


async def hello(name: Annotated[str, Depends(get_name)]):
    return f"hello {name}"
```

What's special is that if the callable object annotated with `Depends(...)` is a generator function, it will be transformed by [`contextlib`](https://docs.python.org/3/library/contextlib.html). The `yield` value is injected into the view, and the cleanup part is executed after the view function exits (whether it returns normally or raises an exception). This is particularly effective when obtaining resources that need to be cleaned up.

```python
async def get_db_connection():
    connection = ...  # get connection
    try:
        yield connection
    finally:
        await connection.close()


async def get_user(db: Annotated[Connection, Depends(get_db_connection)]):
    ...
```

## Usage in Middleware

The usage in middleware is no different. Simply describe it in the parameters.

```python
from typing_extensions import Annotated


def required_auth(endpoint):
    async def wrapper(authorization: Annotated[str, Header()]):
        ...
        return await endpoint()

    return wrapper
```
