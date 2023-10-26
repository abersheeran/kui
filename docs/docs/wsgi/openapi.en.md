Write the following code to access the `/docs/` endpoint on your service to view the generated documentation.

```python
from kui.wsgi import Kui, OpenAPI

app = Kui()

app.router << ("/docs" // OpenAPI().routes)
```

The default documentation template uses [Swagger](https://swagger.io/tools/swagger-ui/). If you prefer the styles of [Redoc](https://github.com/Redocly/redoc) or [RapiDoc](https://mrin9.github.io/RapiDoc/), you can achieve that by changing the `template_name` parameter, for example: `OpenAPI(..., template_name="redoc")`.

Furthermore, you can control the display of any template you like by using the `template` parameter and passing the complete content of the template as a string.

### Tags

In Kui, you can define the `description` value for tags as follows:

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
    If you don't need to add a `description` to a tag, you can skip this step.

Pass the `tags` parameter when registering the route:

```python
from kui.wsgi import Routes

routes = Routes()


@routes.http.get('/', tags=["tag-name", "tag-name-2"])
def handler():
    return "/"
```

## Interface Introduction

For all methods that can handle HTTP requests, their `__doc__` will be used to generate the OpenAPI documentation. The first line will be treated as a summary description, so keep it concise and not too long. After an empty line, the subsequent text will be treated as a detailed description and will be placed in the OpenAPI documentation.

For example:

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

You can also pass parameters when registering routes:

```python
from kui.wsgi import Routes

routes = Routes()


@routes.http.get('/', summary="api summary", description="api description.............")
def handler():
    return "/"
```

If your description is long, you can simply pass the `summary` parameter to the decorator, and the `description` will automatically use the entire `__doc__`.

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

## Describing Request Parameters

When using [dependency injection](./dependency-injection.md), the request parameters will be automatically generated.

### Modifying Content-Type

Kui will automatically read the function signature of `app.factory_class.http.data` and retrieve the `ContentType` objects included in it to generate the Content-Type in the OpenAPI documentation.

Here's a simple custom example that uses `msgpack` to parse data:

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


app = Kui(factory_class=FactoryClass(http=MsgPackRequest))
```

## Describing Response Results

To generate the OpenAPI documentation for response results, you should use [`Annotated`](https://docs.python.org/zh-cn/3/library/typing.html#typing.Annotated) to describe the return value of the view.

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

You can also describe multiple response results as shown below:

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

Using different response subclasses can generate different response result documents.

!!! tip "Default"
    Only the first parameter is required, and the other parameters are optional.

The `headers` parameter in all responses should be a standard [OpenAPI Response](https://github.com/OAI/OpenAPI-Specification/blob/main/versions/3.0.3.md#responseObject) Headers dictionary. For example: `{"Location": {"schema": {"type": "string"}}}`.

- json: `JSONResponse[status_code, headers, content]`
    - `content`: It can be a standard Content dictionary required by [OpenAPI Response](https://github.com/OAI/OpenAPI-Specification/blob/main/versions/3.0.3.md#responseObject), a `TypedDict`, a `str` type, or a subclass of `pydantic.BaseModel`.

- html: `HTMLResponse[status_code, headers]`
- text: `TextResponse[status_code, headers]`
- redirect: `RedirectResponse[status_code, headers]`
- file: `FileResponse[content_type, headers]`
    - `content_type`: Specifies the Content-Type of the returned file.

In addition, you can directly use a standard [OpenAPI Response](https://github.com/OAI/OpenAPI-Specification/blob/main/versions/3.0.3.md#responseObject) dictionary (`dict`) to describe the response results. It will also be parsed and inserted into the final generated API documentation.

### Usage in Middleware

The usage in middleware is no different.

```python
from typing_extensions import Annotated


def required_auth(endpoint):
    def wrapper(authorization: Annotated[str, Header()]) -> Annotated[Any, HttpResponse[401]]:
        ...
        return await endpoint()

    return wrapper
```

### Usage in Dependency Functions

The usage in dependency functions is no different.

```python
from typing_extensions import Annotated


def required_auth(authorization: Annotated[str, Header()]) -> Annotated[Any, HttpResponse[401]]:
    ...
```

## Describing Additional OpenAPI Documentation

You can use `describe_extra_docs` to supplement the OpenAPI documentation descriptions for the corresponding interface. Any description added using `describe_extra_docs` will be merged into the original documentation.

!!! tip ""
    For specific fields, refer to the [OpenAPI Specification](https://github.com/OAI/OpenAPI-Specification/blob/master/versions/3.0.0.md#operationObject).
