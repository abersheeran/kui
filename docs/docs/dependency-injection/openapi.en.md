Write the following code to access the generated documentation on your service at `/docs/`:

```python
from kui.wsgi import Kui, OpenAPI

app = Kui()

app.router << ("/docs" // OpenAPI().routes)
```

The default documentation template uses [Swagger](https://swagger.io/tools/swagger-ui/). If you prefer the styles of [Redoc](https://github.com/Redocly/redoc) or [RapiDoc](https://mrin9.github.io/RapiDoc/), you can achieve that by changing the `template_name`. For example: `OpenAPI(..., template_name="redoc")`.

Furthermore, you can control the display of any template by using the `template` parameter. Just pass the complete content of the template as a string to the `template` parameter.

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

Pass the `tags` parameter when registering routes:

```python
from kui.wsgi import Routes

routes = Routes()


@routes.http.get('/', tags=["tag-name", "tag-name-2"])
def handler():
    return "/"
```

## Interface Introduction

For all methods that can handle HTTP requests, their `__doc__` will be used to generate the OpenAPI documentation. The first line will be treated as a summary description, so keep it concise and not too long. After an empty line, the subsequent text will be considered as detailed description and will be placed in the OpenAPI documentation.

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

You can also pass parameters when registering routes.

!!! tip
    When passing parameters, they will override the content parsed from `__doc__`.

```python
from kui.wsgi import Routes

routes = Routes()


@routes.http.get('/', summary="api summary", description="api description.............")
def handler():
    return "/"
```

## Describe Request Parameters

When using [Dependency Injection](./index.md), request parameters will be generated automatically.

### Modify Content-Type

Kui will automatically read the function signature of `app.factory_class.http.data` and extract the `ContentType` objects included in it to generate the Content-Type in the OpenAPI documentation.

Here's a simple customization example - using `msgpack` to parse data:

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

## Describe Response Results

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

!!! tip
    Only the first parameter is required, and the other parameters are optional.

The `headers` parameter in all responses should be a standard [OpenAPI Response](https://github.com/OAI/OpenAPI-Specification/blob/main/versions/3.0.3.md#responseObject) Headers dictionary. For example: `{"Location": {"schema": {"type": "string"}}}`.

- json: `JSONResponse[status_code, headers, content]`
    - `content`: It can be a standard Content dictionary required by [OpenAPI Response](https://github.com/OAI/OpenAPI-Specification/blob/main/versions/3.0.3.md#responseObject), a `TypedDict`, a `str`, or a subclass of `pydantic.BaseModel`.

- html: `HTMLResponse[status_code, headers]`
- text: `TextResponse[status_code, headers]`
- redirect: `RedirectResponse[status_code, headers]`
- file: `FileResponse[content_type, headers]`
    - `content_type`: Specifies the Content-Type of the returned file.

In addition, you can also directly use a standard [OpenAPI Response](https://github.com/OAI/OpenAPI-Specification/blob/main/versions/3.0.3.md#responseObject) dictionary (`dict`) to describe the response result. It will be parsed and inserted into the final generated API documentation.

### Using in Middleware

Just like using in view functions, you can use `Annotated` to describe the response result in middleware.

```python
from typing_extensions import Annotated


def required_auth(endpoint):
    def wrapper(authorization: Annotated[str, Header()]) -> Annotated[Any, JSONResponse[401]]:
        ...
        return await endpoint()

    return wrapper
```

### Using in Dependency Functions

Just like using in view functions, you can use `Annotated` to describe the response result in dependency functions.

```python
from typing_extensions import Annotated


def required_auth(authorization: Annotated[str, Header()]) -> Annotated[Any, JSONResponse[401]]:
    ...
```

## Describe Additional OpenAPI Documentation

You can use `describe_extra_docs` to supplement the OpenAPI documentation description for the corresponding interface. Any descriptions added through `describe_extra_docs` will be merged into the original documentation.

!!! tip ""
    Refer to the [OpenAPI Specification](https://github.com/OAI/OpenAPI-Specification/blob/master/versions/3.0.0.md#operationObject) for specific fields.
