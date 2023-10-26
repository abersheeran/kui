Let's start with a simple example that involves two pagination parameters. First, we annotate them with the `int` type using Type hints and provide `Query(...)` as an additional type description.

The `Query` indicates that the values will be read from `request.query_params`. The `...` as the first parameter means that it has no default value, so the client must provide a value when requesting this API. For example: `?page_num=1&page_size=10`.

If you use `Query(10)`, it means that this value can be omitted by the frontend, and its default value will be `10`.

```python
from typing_extensions import Annotated
from kui.wsgi import Query


def getlist(
    page_num: Annotated[int, Query(...)],
    page_size: Annotated[int, Query(...)],
):
    ...
```

Alternatively, you can use a class that inherits from `pydantic.BaseModel` as a type annotation to describe parameters of the same type. The following example is equivalent to the previous one.

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

Similarly, you can use other objects to retrieve corresponding parts of the parameters. Here's a comparison:

- `Path`: `request.path_params`
- `Query`: `request.query_params`
- `Header`: `request.headers`
- `Cookie`: `request.cookies`
- `Body`: `request.data()`

!!! tip "Path Parameter Validation Failure"

    Path parameter (`Path`) validation errors are handled differently. It will attempt to call the user-registered 404 exception handler or the default 404 exception handler to return a 404 status, as if the route was not found, instead of returning a 422 status like other parameter validation errors.

!!! tip "Using in Middleware"

    ```python
    from typing_extensions import Annotated


    def required_auth(endpoint):
        def wrapper(authorization: Annotated[str, Header()]):
            ...
            return endpoint()

        return wrapper
    ```

## File Upload

Kuí provides the `UploadFile` class to describe file upload parameters.

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

!!! tip "OpenAPI Documentation"
    This will also generate OpenAPI documentation `{"type": "string", "format": "binary"}`.
