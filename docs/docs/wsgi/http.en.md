## Handlers

In the following text, the callable object used to process HTTP requests is referred to as an HTTP processor.

### Function Handlers

Using a function to handle requests is straightforward.

```python
from kui.wsgi import Kui

app = Kui()


@app.router.http("/hello")
def hello():
    return "hello"
```

The `@app.router.http` decorator returns the original function, so the same function can be registered under multiple routes.

```python
from kui.wsgi import Kui, request

app = Kui()


@app.router.http("/hello", name="hello")
@app.router.http("/hello/{name}", name="hello-with-name")
def hello():
    if request.path_params:
        return f"hello {request.path_params['name']}"
    return "hello"
```

You can use `required_method` to restrict the function processor to accept only specified request methods.

```python
from kui.wsgi import Kui, request, required_method

app = Kui()


@app.router.http("/hello", middlewares=[required_method("POST")])
def need_post():
    return request.method
```

!!! notice
    When you use `required_method` to constrain the request methods, the `OPTIONS` method will be automatically handled.

!!! notice
    When you allow the `GET` method using `required_method`, the `HEAD` method will also be allowed.

### Class Handlers

Using a class to handle multiple types of requests is simple. Just inherit from `HttpView` and write the corresponding methods. The supported methods are `"get"`, `"post"`, `"put"`, `"patch"`, `"delete"`, `"head"`, `"options"`, and `"trace"`.

!!! tip "Allow more request methods"
    Override the class attribute `HTTP_METHOD_NAMES` when inheriting the class.

```python
from kui.wsgi import Kui, request, HttpView

app = Kui()


@app.router.http("/cat")
class Cat(HttpView):
    @classmethod
    def get(cls):
        return request.method

    @classmethod
    def post(cls):
        return request.method

    @classmethod
    def put(cls):
        return request.method

    @classmethod
    def patch(cls):
        return request.method

    @classmethod
    def delete(cls):
        return request.method
```

## Getting Request Values

Use the following statement to access the global variable `request`, which is a proxy object that allows reading, writing, and deleting various attributes of the `HttpRequest` object corresponding to the current request.

```python
from kui.wsgi import request


def homepage():
    return request.url.path
```

In general, this is sufficient for most use cases. However, if you really need to access the original `HttpRequest` object, you can use

```python
from kui.wsgi import request_var


def endpoint():
    request = request_var.get()
    ...
```

Here are the commonly used attributes and methods of the `kui.wsgi.HttpRequest` object.

### Method

You can use `request.method` to retrieve the request method, such as `GET` or `POST`.

### URL

You can use `request.url` to retrieve the request path. This attribute is an object similar to a string that exposes all the components parsed from the URL.

For example: `request.url.path`, `request.url.port`, `request.url.scheme`

### Path Parameters

`request.path_params` is a dictionary that contains all the parsed path parameters.

### Headers

`request.headers` is a case-insensitive multi-value dictionary.

The `key` obtained from `request.headers.keys()`/`request.headers.items()` will be in lowercase.

#### Accept

By reading the `request.accepted_types` attribute, you can obtain all the response types accepted by the client.

By calling the `request.accepts` function, you can determine what response types the client accepts. For example: `request.accepts("text/html")`.

#### Content Type

Use `request.content_type` to retrieve the `Content-Type` header.

#### Content Length

Use `request.content_length` to retrieve the `Content-Length` header.

#### Date

Use `request.date` to retrieve the `Date` header.

#### Referrer

Use `request.referrer` to retrieve the `Referer` header.

### Query Parameters

`request.query_params` is a multi-value dictionary.

For example: `request.query_params['search']`

### Client Address

`request.client` is a `namedtuple` defined as `namedtuple("Address", ["host", "port"])`.

To get the client's hostname or IP address: `request.client.host`.

To get the port the client is using in the current connection: `request.client.port`.

!!!notice
    Any element in the tuple may be `None`. This depends on the values passed by the server.

### Cookies

`request.cookies` is a standard dictionary defined as `Dict[str, str]`.

For example: `request.cookies.get('mycookie')`

### Body

There are several ways to read the request body:

- `request.body`: Returns a `bytes` object.

- `request.form`: Parses the body as a form and returns the result as a multi-value dictionary.

- `request.json`: Parses the body as a JSON string and returns the result.

- `request.data()`: Parses the body based on the information provided by the `content_type` and returns the result.

You can also use the `for` loop syntax to read the body as a `bytes` stream:

```python
def post():
    ...
    body = b''
    for chunk in request.stream():
        body += chunk
    ...
```

If you directly use `request.stream()` to read the data, the request body will not be cached in memory. Any subsequent calls to `.body`/`.form`/`.json` will throw an error.

### Request Files

You can parse form data received in the `multipart/form-data` format, including files, using `request.form`.

Files will be wrapped in the `baize.datastructures.UploadFile` object, which has the following attributes:

* `filename: str`: The original filename of the submitted file (e.g., `myimage.jpg`).
* `content_type: str`: The file type (MIME type / media type) (e.g., `image/jpeg`).
* `headers: Headers`: The headers carried by the file field in the `multipart/form-data` format.
* `file: tempfile.SpooledTemporaryFile`: The temporary file that stores the file content (you can read and write to this object directly, but it is better not to).

`UploadFile` also has five methods:

* `write(data: bytes) -> None`: Write data to the file.
* `read(size: int) -> bytes`: Read data from the file.
* `seek(offset: int) -> None`: Move the file pointer to the specified position.
* `save(filepath: str) -> None`: Save the file to the specified path on disk.
* `close() -> None`: Close the file.

### State

In some cases, you may need to store additional custom information in `request`. You can use `request.state` for storage.

```python
request.state.user = User(name="Alice")  # Write

user_name = request.state.user.name  # Read

del request.state.user  # Delete
```

## Returning Response Values

For any successfully processed HTTP request, you must return an `HttpResponse` object or one of its subclasses.

### HttpResponse

Signature: `HttpResponse(status_code: int = 200, headers: Mapping[str, str] = None)`

* `status_code` - The HTTP status code.
* `headers` - A dictionary of strings.

#### Set Cookie

`HttpResponse` provides the `set_cookie` method to allow you to set cookies.

Signature: `HttpResponse.set_cookie(key, value="", max_age=None, expires=None, path="/", domain=None, secure=False, httponly=False, samesite="lax")`

* `key: str` - The key that will become the cookie.
* `value: str = ""` - The value of the cookie.
* `max_age: int` - The lifetime of the cookie in seconds. Non-positive integers will cause the cookie to be discarded immediately.
* `expires: Optional[int]` - The number of seconds before the cookie expires.
* `path: str = "/"` - The subset of routes to which the cookie will apply.
* `domain: Optional[str]` - The domain to which the cookie is valid.
* `secure: bool = False` - Indicates that the cookie should only be sent to the server when using the HTTPS protocol.
* `httponly: bool = False` - Indicates that the cookie cannot be accessed via JavaScript using properties such as `Document.cookie`, `XMLHttpRequest`, or `Request`.
* `samesite: str = "lax"` - Specifies the SameSite policy for the cookie. Valid values are `"lax"`, `"strict"`, and `"none"`.

#### Delete Cookie

`HttpResponse` also provides the `delete_cookie` method to expire a previously set cookie.

Signature: `HttpResponse.delete_cookie(key, path='/', domain=None, secure=False, httponly=False, samesite="lax")`

### PlainTextResponse

Accepts a `str` or `bytes` and returns a plain text response.

```python
from kui.wsgi import PlainTextResponse


def return_plaintext():
    return PlainTextResponse('Hello, world!')
```

### HTMLResponse

Accepts a `str` or `bytes` and returns an HTML response.

```python
from kui.wsgi import HTMLResponse


def return_html():
    return HTMLResponse('<html><body><h1>Hello, world!</h1></body></html>')
```

### JSONResponse

Accepts a Python object and returns a response encoded as `application/json`.

```python
from kui.wsgi import JSONResponse


def return_json():
    return JSONResponse({'hello': 'world'})
```

`JSONResponse` exposes all the options of `json.dumps` as keyword arguments for customization.

### RedirectResponse

Returns an HTTP redirect. By default, it uses the 307 status code.

```python
from kui.wsgi import RedirectResponse


def return_redirect():
    return RedirectResponse('/')
```

### StreamResponse

Accepts a generator and streams the response body.

```python
import time
from kui.wsgi import StreamResponse


def slow_numbers(minimum, maximum):
    yield b'<html><body><ul>'
    for number in range(minimum, maximum + 1):
        yield f'<li>{number}</li>'.encode()
        time.sleep(0.5)
    yield b'</ul></body></html>'


def return_stream(environ, start_response):
    generator = slow_numbers(1, 10)
    return StreamResponse(generator, content_type='text/html')
```

### FileResponse

Transmits a file as the response.

Compared to other response types, it is instantiated with different parameters:

* `filepath` - The file path of the file to be streamed.
* `headers` - The same as the `headers` parameter in `Response`.
* `content_type` - The MIME media type of the file. If not set, the file name or path will be used to infer the media type.
* `download_name` - If set, it will be included in the `Content-Disposition` of the response.
* `stat_result` - Accepts an `os.stat_result` object. If not passed, the result of `os.stat(filepath)` will be used automatically.

`FileResponse` automatically sets the appropriate `Content-Length`, `Last-Modified`, and `ETag` headers. And it supports [file range requests](https://developer.mozilla.org/en-US/docs/Web/HTTP/Range_requests) without any additional handling.

### TemplateResponse

`TemplateResponse` is a shortcut for `app.templates.TemplateResponse`.

#### Jinja2 Template Engine

Kuí provides built-in support for Jinja2 templates. As long as you have installed the `jinja2` module, you can export `Jinja2Templates` from `kui.wsgi.templates`. Here is a simple example: when accessing "/", it will look for the `homepage.html` file in the `templates` directory at the root of the project for rendering.

```python
from kui.wsgi import Kui, TemplateResponse, Jinja2Templates

app = Kui(templates=Jinja2Templates("templates"))


@app.router.http("/")
def homepage():
    return TemplateResponse("homepage.html")
```

If you want to use a specific folder in a module for template files, you can use `Jinja2Templates("module_name:dirname")`.

You can also pass multiple directories for Jinja2 to search in order until it finds the first available template. For example: `Jinja2Templates("templates", "module_name:dirname")`.

#### Other Template Engines

Implement the `kui.wsgi.templates.BaseTemplates` interface to create your own template engine class.

### SendEventResponse

You can return a [Server-sent Events](https://developer.mozilla.org/en-US/docs/Server-sent_events/Using_server-sent_events) response using `SendEventResponse`. This is a type of HTTP long-polling response that can be used for scenarios such as server-side real-time data pushing to clients.

`SendEventResponse` accepts a generator that generates messages. Each message `yielded` by the generator should be a valid Server-Sent Events message.

Here is an example that sends a "hello" message every second, with a total of 101 messages.

```python
import time
from typing import Generator
from kui.wsgi import Kui, SendEventResponse, ServerSentEvent

app = Kui()


@app.router.http("/message")
def message():
    def message_gen() -> Generator[ServerSentEvent, None, None]:
        for i in range(101):
            time.sleep(1)
            yield {"id": i, "data": "hello"}

    return SendEventResponse(message_gen())
```

!!! tip "Frontend Web Development"
    In most cases, using the browser's built-in [EventSource](https://developer.mozilla.org/en-US/docs/Web/API/EventSource) is sufficient. However, in more complex scenarios such as using the Server-sent events with the ChatGPT API provided by OpenAI, you can use [@microsoft/fetch-event-source](https://github.com/Azure/fetch-event-source) to achieve more advanced functionality.

### Simplified Response Writing

For convenience, Kuí allows you to define custom functions to handle non-`HttpResponse` objects returned by HTTP processors. The mechanism intercepts the response and automatically selects the handling function based on the type of the response value, converting non-`HttpResponse` objects into `HttpResponse` objects.

!!! tip "Explicit Conversion"
    If you need to convert the return value of a function to an `HttpResponse` object, you can use `kui.wsgi.convert_response`.

In the following example, the view function returns a `dict` object, but the client receives a JSON response. This is because Kuí provides some handling functions for common types:

- `dict | tuple | list`: Automatically converted to `JSONResponse`
- `str | bytes`: Automatically converted to `PlainTextResponse`
- `types.GeneratorType`: Automatically converted to `SendEventResponse`
- `pathlib.PurePath`: Automatically converted to `FileResponse`
- `baize.datastructures.URL`: Automatically converted to `RedirectResponse`

```python
def get_detail():
    return {"key": "value"}
```

You can also return multiple values to customize the HTTP status and headers:

```python
def not_found():
    return {"message": "Not found"}, 404


def no_content():
    return "", 301, {"location": "https://kui.aber.sh"}
```

Similarly, you can define the simplified writing of response values to standardize the response format of the project (even though `TypedDict` has weak constraints in Python, `dataclass` is much more effective). The following example demonstrates that when you return an `Error` object in a view function, it will be automatically converted to a `JSONResponse`, and the default status code is `400`:

```python
from dataclasses import dataclass, asdict
from typing import Mapping
from kui.wsgi import Kui, HttpResponse, JSONResponse

app = Kui()


@dataclass
class Error:
    code: int = 0
    title: str = ""
    message: str = ""


@app.response_convertor.register(Error)
def _error_json(error: Error, status: int = 400, headers: Mapping[str, str] = None) -> HttpResponse:
    return JSONResponse(asdict(error), status, headers)
```

It is equivalent to:

```python
from dataclasses import dataclass, asdict
from typing import Mapping
from kui.wsgi import Kui, HttpResponse, JSONResponse


@dataclass
class Error:
    code: int = 0
    title: str = ""
    message: str = ""


def _error_json(error: Error, status: int = 400, headers: Mapping[str, str] = None) -> HttpResponse:
    return JSONResponse(asdict(error), status, headers)


app = Kui(
    response_converters={
        Error: _error_json
    }
)
```

You can also override the default conversion method. The following example is equivalent to the previous example:

```python
from typing import Mapping
from kui.wsgi import Kui, HttpResponse

app = Kui()


@app.response_convertor.register(tuple)
@app.response_convertor.register(list)
@app.response_convertor.register(dict)
def _more_json(body, status: int = 200, headers: Mapping[str, str] = None) -> HttpResponse:
    return CustomizeJSONResponse(body, status, headers)
```

## Exception Handling

### HTTPException

The parameter signature is: `HTTPException(status_code: int, headers: dict = None, content: typing.Any = None)`

You can use `HTTPException` to return an HTTP response by raising it (don't worry, Kuí will convert it into a regular response object). If you don't provide a `content` value, it will use `http.HTTPStatus(status_code).description` from the Python standard library as the final result.

```python
from kui import HTTPException


def endpoint():
    ...
    raise HTTPException(400)
    ...
```

Sometimes you may want to return more information. You can pass `content` and `headers` parameters to control the actual response object, just like using `HttpResponse`. Here's a simple example:

```python
from kui import HTTPException


def endpoint():
    ...
    raise HTTPException(405, headers={"Allow": "HEAD, GET, POST"})
    ...
```

!!! tip
    If you want to raise an `HTTPException` in a `lambda` function, you can use `baize.exceptions.abort`.

### Custom Exception Handling

For intentionally thrown exceptions, Kuí provides a method for unified handling.

You can catch specific HTTP status codes, so when dealing with an `HTTPException` that contains the corresponding HTTP status code, Kuí will use the function you defined instead of the default behavior. You can also catch other exceptions that inherit from `Exception` and return specific content to the client through a custom function.

```python
from kui.wsgi import Kui, HTTPException, HttpResponse, PlainTextResponse

app = Kui()


@app.exception_handler(404)
def not_found(exc: HTTPException) -> HttpResponse:
    return PlainTextResponse("what do you want to do?", status_code=404)


@app.exception_handler(ValueError)
def value_error(exc: ValueError) -> HttpResponse:
    return PlainTextResponse("Something went wrong with the server.", status_code=500)
```

In addition to decorator registration, you can also use a list-based registration method. The following example is equivalent to the previous one:

```python
from kui.wsgi import Kui, HTTPException, HttpResponse, PlainTextResponse


def not_found(exc: HTTPException) -> HttpResponse:
    return PlainTextResponse("what do you want to do?", status_code=404)


def value_error(exc: ValueError) -> HttpResponse:
    return PlainTextResponse("Something went wrong with the server.", status_code=500)


app = Kui(exception_handlers={
    404: not_found,
    ValueError: value_error,
})
```

## Allowing Cross-Origin Requests

To solve the cross-origin issue in modern browsers, [Cross-Origin Resource Sharing](https://developer.mozilla.org/en-US/docs/Web/HTTP/CORS) is generally used. In Kuí, you can quickly configure API to allow cross-origin requests using the following code:

```python
from kui.wsgi import Routes, allow_cors

routes = Routes(..., http_middlewares=[allow_cors()])
```

`allow_cors` has the following parameters:

- `allow_origins: Iterable[Pattern]`: Allowed origins. It requires `re.compile` precompiled `Pattern` objects. The default value is `(re.compile(".*"), )`.
- `allow_methods: Iterable[str]`: Allowed request methods. The default value is `("GET", "POST", "PUT", "PATCH", "DELETE", "HEAD", "OPTIONS", "TRACE")`.
- `allow_headers: Iterable[str]`: Allowed request headers. Corresponds to [`Access-Control-Allow-Headers`](https://developer.mozilla.org/en-US/docs/Web/HTTP/Headers/Access-Control-Allow-Headers).
- `expose_headers: Iterable[str]`: Request headers that can be listed in the response. Corresponds to [`Access-Control-Expose-Headers`](https://developer.mozilla.org/en-US/docs/Web/HTTP/Headers/Access-Control-Expose-Headers).
- `allow_credentials: bool`: If `True`, allows cross-origin requests to carry cookies; otherwise, it does not allow. The default value is `False`.
- `max_age: int`: Cache time for preflight requests. The default value is `600` seconds.

If you need to enable CORS globally, you can pass the `cors_config` parameter to `Kui`. It is a dictionary with the same key-value pairs as the `allow_cors` parameters.

```python
from kui.wsgi import Kui

app = Kui(cors_config={})
```
