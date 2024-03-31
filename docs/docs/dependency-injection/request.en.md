You can use type annotations to obtain the requested parameters, and Kui will automatically validate the parameters and return error messages. Here is a simple and common example of pagination parameters:

```python
from typing_extensions import Annotated
from kui.wsgi import Query

def getlist(
    page_num: Annotated[int, Query(...)],
    page_size: Annotated[int, Query(...)],
):
    ...
```

Sometimes the frontend may request parameter names in camelCase, while PEP8 recommends Python programs to use snake_case. In such cases, you can use the `alias` parameter to specify the parameter name.

```python
from typing_extensions import Annotated
from kui.wsgi import Query

def getlist(
    page_num: Annotated[int, Query(..., alias="pageNum")],
    page_size: Annotated[int, Query(..., alias="pageSize")],
):
    ...
```

You can also specify default values for parameters, so that the default value will be used when the frontend does not provide the corresponding parameter.

```python
from typing_extensions import Annotated
from kui.wsgi import Query

def getlist(
    page_num: Annotated[int, Query(1)],
    page_size: Annotated[int, Query(10)],
):
    ...
```

When generating documentation, you may want to provide some information about the parameters to the users of this API. In this case, you can use the `title` and `description` parameters.

```python
from typing_extensions import Annotated
from kui.wsgi import Query

def getlist(
    page_num: Annotated[int, Query(..., title="Page Num", description="page num")],
    page_size: Annotated[int, Query(..., title="Page Size", description="page size")],
):
    ...
```



Similarly, you can use other objects to obtain the corresponding parts of the parameters, as follows:

- `Path`: `request.path_params`
- `Query`: `request.query_params`
- `Header`: `request.headers`
- `Cookie`: `request.cookies`
- `Body`: `request.data()`

!!! tip "Path Parameter Validation Failure"

    Path parameter (`Path`) validation errors are somewhat special. It will attempt to call the user's own registered 404 exception handling method or the default 404 exception handling method to return a 404 status, just like not finding a route, instead of returning a 422 status like other parameter validation errors.

!!! tip "Using a Model to Parse Request Body"

    Sometimes you may want to use a model to parse the request body, in which case you can specify `Body(..., exclusive=True)`.

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

## Using in Middleware

Using parameter validation in middleware is no different.

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
    This will also automatically generate OpenAPI documentation `{"type": "string", "format": "binary"}`.
