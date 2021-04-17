## HTTP 处理器

在下文中，用于处理 HTTP 请求的可调用对象被称为 HTTP 处理器。

### 函数处理器

使用函数处理请求是很简单的。

```python
from indexpy import Index

app = Index()


@app.router.http("/hello")
async def hello():
    return "hello"
```

`@app.router.http` 装饰器将返回原始的函数，故而可以将同一个函数注册到多个路由下。

```python
from indexpy import Index, request

app = Index()


@app.router.http("/hello", name="hello")
@app.router.http("/hello/{name}", name="hello-with-name")
async def hello():
    if request.path_params:
        return f"hello {request.path_params['name']}"
    return "hello"
```

你还可以使用 `required_method` 来约束函数处理器仅接受指定的请求方法。

```python
from indexpy import Index, request, required_method

app = Index()


@app.router.http("/hello")
@required_method("POST")
async def need_post():
    return request.method
```

!!! tip ""
    当你使用 `required_method` 对请求方法进行约束时，`OPTIONS` 方法将会被自动处理。

!!! notice ""
    当你使用 `required_method` 允许 `GET` 方法时，`HEAD` 方法也会同时被允许。

### 类处理器

使用类处理多种请求十分简单。只需要继承 `HttpView` 并编写对应的方法，支持的方法有 `"get"`，`"post"`，`"put"`，`"patch"`，`"delete"`，`"head"`，`"options"`，`"trace"`。

!!! tip "允许更多请求方法"
    在继承类时覆盖类属性 `HTTP_METHOD_NAMES` 即可。

```python
from indexpy import Index, request, HttpView

app = Index()


@app.router.http("/cat")
class Cat(HttpView):

    async def get(self):
        return request.method

    async def post(self):
        return request.method

    async def put(self):
        return request.method

    async def patch(self):
        return request.method

    async def delete(self):
        return request.method
```

## 获取请求值

使用 `from indexpy import request` 语句获取全局变量 `request`，它是一个代理对象，可以读写删当前请求对应的 `Request` 对象的各个属性。一般来说这足以应付大部分需求，但如果你真的需要访问原始 `Request` 对象，可以使用 `indexpy.requests.request_var.get()`。

以下是 `indexpy.requests.Request` 对象的常用属性与方法。

### Method

通过 `request.method` 可以获取到请求方法，例如 `get`/`post` 等。

### URL

通过 `request.url` 可以获取到请求路径。该属性是一个类似于字符串的对象，它公开了可以从URL中解析出的所有组件。

例如：`request.url.path`, `request.url.port`, `request.url.scheme`

### Path Parameters

`request.path_params` 是一个字典，包含所有解析出的路径参数。

### Headers

`request.headers` 是一个大小写无关的多值字典(multi-dict)。但通过 `request.headers.keys()`/`request.headers.items()` 取出来的 `key` 均为小写。

#### Accept

通过读取 `request.accepted_types` 属性你可以获取客户端接收的全部响应类型。

通过调用 `request.accepts` 函数你可以判断客户端接受什么样的响应类型。例如：`request.accepts("text/html")`。

#### Content Type

你可以使用 `request.content_type == "application/json"` 之类的语句来判断请求类型是否满足条件。不必考虑现实中的 HTTP 请求头 `Content-Type: application/json; charset=utf-8` 尾部的 `; charset=utf-8` 会影响判断的准确性，这类选项会被以字典形式解析到 `request.content_type.options`。

### Query Parameters

`request.query_params` 是一个不可变的多值字典(multi-dict)。

例如：`request.query_params['search']`

### Client Address

`request.client` 是一个 `namedtuple`，定义为 `namedtuple("Address", ["host", "port"])`。

获取客户端 hostname 或 IP 地址: `request.client.host`。

获取客户端在当前连接中使用的端口: `request.client.port`。

!!!notice ""
    元组中任何一个元素都可能为 None。这受限于 ASGI 服务器传递的值。

### Cookies

`request.cookies` 是一个标准字典，定义为 `Dict[str, str]`。

例如：`request.cookies.get('mycookie')`

### Body

有几种方法可以读到请求体内容：

- `await request.body`：返回一个 `bytes`。

- `await request.form`：将 `body` 作为表单进行解析并返回结果（多值字典）。

- `await request.json`：将 `body` 作为 JSON 字符串解析并返回结果。

- `await request.data`：将 `body` 根据 `content_type` 提供的信息进行解析并返回。

你也可以使用 `async for` 语法将 `body` 作为一个 `bytes` 流进行读取：

```python
async def post():
    ...
    body = b''
    async for chunk in request.stream():
        body += chunk
    ...
```

如果你直接使用了 `request.stream()` 去读取数据，那么请求体将不会缓存在内存中。其后任何对 `.body`/`.form`/`.json` 的调用都将抛出错误。

在某些情况下，例如长轮询或流式响应，你可能需要确定客户端是否已断开连接。可以使用 `disconnected = await request.is_disconnected()` 确定此状态。

### Request Files

通过 `await request.form` 可以解析通过 `multipart/form-data` 格式接收到的表单，包括文件。

文件将被包装为 `starlette.datastructures.UploadFile` 对象，它有如下属性：

* `filename: str`: 被提交的原始文件名称 (例如 `myimage.jpg`).
* `content_type: str`: 文件类型 (MIME type / media type) (例如 `image/jpeg`).
* `file: tempfile.SpooledTemporaryFile`: 存储文件内容的临时文件（可以直接读写这个对象，但最好不要）。

`UploadFile` 还有四个异步方法：

* `async write(data: Union[str, bytes])`: 写入数据到文件中。
* `async read(size: int)`: 从文件中读取数据。
* `async seek(offset: int)`: 文件指针跳转到指定位置。
* `async close()`: 关闭文件。

下面是一个读取原始文件名称和内容的例子：

```python
form = await request.form
filename = form["upload_file"].filename
contents = await form["upload_file"].read()
```

### State

某些情况下需要储存一些额外的自定义信息到 `request` 中，可以使用 `request.state` 用于存储。

```python
request.state.user = User(name="Alice")  # 写

user_name = request.state.user.name  # 读

del request.state.user  # 删
```

## 返回响应值

对于任何正常处理的 HTTP 请求都必须返回一个 `HttpResponse` 对象或者是它的子类对象。

### HttpResponse

签名：`HttpResponse(status_code: int = 200, headers: Mapping[str, str] = None)`

* `status_code` - HTTP 状态码。
* `headers` - 字符串字典。

#### Set Cookie

`HttpResponse` 提供 `set_cookie` 方法以允许你设置 cookies。

签名：`HttpResponse.set_cookie(key, value="", max_age=None, expires=None, path="/", domain=None, secure=False, httponly=False, samesite="lax")`

* `key: str`，将成为 Cookie 的键。
* `value: str = ""`，将是 Cookie 的值。
* `max_age: Optional[int]`，以秒为单位定义 Cookie 的生存期。非正整数会立即丢弃 Cookie。
* `expires: Optional[int]`，它定义 Cookie 过期之前的秒数。
* `path: str = "/"`，它指定 Cookie 将应用到的路由的子集。
* `domain: Optional[str]`，用于指定 Cookie 对其有效的域。
* `secure: bool = False`，指示仅当使用 HTTPS 协议发出请求时，才会将 Cookie 发送到服务器。
* `httponly: bool = False`，指示无法通过 Javascript 通过 `Document.cookie` 属性、`XMLHttpRequest` 或 `Request` 等 API 来访问 Cookie。
* `samesite: str = "lax"`，用于指定 Cookie 的相同网站策略。有效值为 `"lax"`，`"strict"` 和 `"none"`。

#### Delete Cookie

`HttpResponse` 也提供了 `delete_cookie` 方法指定已设置的 Cookie 过期。

签名: `HttpResponse.delete_cookie(key, path='/', domain=None)`

### PlainTextResponse

接受 `str` 或 `bytes` 并返回纯文本响应。

```python
from indexpy import PlainTextResponse


async def return_plaintext():
    return PlainTextResponse('Hello, world!')
```

### HTMLResponse

接受 `str` 或 `bytes` 并返回 HTML 响应。

```python
from indexpy import HTMLResponse


async def return_html():
    return HTMLResponse('<html><body><h1>Hello, world!</h1></body></html>')
```

### JSONResponse

接受一些 Python 对象并返回一个 `application/json` 编码的响应。

```python
from indexpy import JSONResponse


async def return_json():
    return JSONResponse({'hello': 'world'})
```

`JSONResponse` 以关键词参数的形式暴露出全部 `json.dumps` 的选项以供自定义。例如在很多时候，Python 内置的 `json` 转换器无法满足实际项目的序列化需求，可以通过覆盖 `default` 方法来自定义无法序列化的对象该如何处理。

```python
import json
import decimal
import datetime

from indexpy import JSONResponse


def custom_convert(obj):
    if isinstance(obj, datetime.datetime):
        return obj.strftime("%Y-%m-%d %H:%M:%S")

    if isinstance(obj, datetime.date):
        return obj.strftime("%Y-%m-%d")

    if isinstance(obj, decimal.Decimal):
        return str(obj)

    raise TypeError(f'Object of type {obj.__class__.__name__} is not JSON serializable')


async def return_json():
    return JSONResponse({'hello': 'world'}, default=custom_convert)
```

### RedirectResponse

返回 HTTP 重定向。默认情况下使用 307 状态代码。

```python
from indexpy import RedirectResponse


async def return_redirect():
    return RedirectResponse('/')
```

### StreamResponse

接受一个异步生成器，流式传输响应主体。

```python
import asyncio

from indexpy import StreamingResponse


async def slow_numbers(minimum, maximum):
    yield('<html><body><ul>')
    for number in range(minimum, maximum + 1):
        yield '<li>%d</li>' % number
        await asyncio.sleep(0.5)
    yield('</ul></body></html>')


async def return_stream(scope, receive, send):
    generator = slow_numbers(1, 10)
    return StreamingResponse(generator, content_type='text/html')
```

### FileResponse

异步传输文件作为响应。

与其他响应类型相比，采用不同的参数进行实例化：

* `filepath` - 要流式传输的文件的文件路径。
* `headers` - 与 `Response` 中的 `headers` 参数的作用相同。
* `media_type` - 文件的 MIME 媒体类型。如果未设置，则文件名或路径将用于推断媒体类型。
* `download_name` - 如果设置此参数，它将包含在响应的 `Content-Disposition` 中。
* `stat_result` - 接受一个 `os.stat_result` 对象，如果不传入则会自动使用 `os.stat(filepath)` 的结果。

`FileResponse` 将自动设置适当的 `Content-Length`、`Last-Modified` 和 `ETag` 标头。并且无需任何额外的处理即可支持[文件范围请求](https://developer.mozilla.org/zh-CN/docs/Web/HTTP/Range_requests)。

### TemplateResponse

`TemplateResponse` 是 `app.templates.TemplateResponse` 的一个快捷方式。

#### Jinja2 模板引擎

Index-py 内置了对 Jinja2 模板的支持，只要你安装了 `jinja2` 模块，就能从 `indexpy.templates` 中导出 `Jinja2Templates`。以下是一个简单的使用样例，访问 "/" 它将从项目根目录下的 templates 目录寻找 homepage.html 文件进行渲染。

```python
from indexpy import Index, TemplateResponse
from indexpy.http.templates import Jinja2Templates

app = Index(templates=Jinja2Templates("templates"))


@app.router.http("/")
async def homepage():
    return TemplateResponse("homepage.html")
```

如果你要使用某个模块下的指定文件夹中的模板文件，可以使用 `Jinja2Templates("module_name:dirname")`。你还可以传递多个目录让 Jinja2 按照顺序依次查找，直到找到第一个可用的模板，例如：`Jinja2Templates("templates", "module_name:dirname")`。

#### 其他模板引擎

通过继承 `indexpy.templates.BaseTemplates` 并实现 `TemplateResponse` 方法，你可以实现自己的模板引擎类。

### SendEventResponse

通过 `SendEventResponse` 可以返回一个 [Server-sent Events](https://developer.mozilla.org/zh-CN/docs/Server-sent_events/Using_server-sent_events) 响应，这是一种 HTTP 长连接响应，可应用于服务器实时推送数据到客户端等场景。

`SendEventResponse` 除了可以接受诸如 `status_code`、`headers` 等常规参数外，还需要自行传入一个用于生成消息的异步生成器。传入的异步生成器 `yield` 的每一条消息都需要为合规的 Server-Sent Event 消息（`indexpy.ServerSentEvent` 类型）。

如下是一个每隔一秒发送一条 hello 消息、一共发送一百零一条消息的样例。

```python
import asyncio

from indexpy import Index, SendEventResponse

app = Index()


@app.router.http("/message")
async def message():

    async def message_gen():
        for i in range(101):
            await asyncio.sleep(1)
            yield {"id": i, "data": "hello"}

    return SendEventResponse(message_gen())
```

### 响应的简化写法

为了方便使用，Index-py 允许自定义一些函数来处理 HTTP 处理器返回的非 `HttpResponse` 对象。它的原理是拦截响应，通过响应值的类型来自动选择处理函数，把非 `HttpResponse` 对象转换为 `HttpResponse` 对象。

!!! tip ""
    如果需要手动把函数的返回值转换为 `HttpResponse` 对象，则可以使用 `indexpy.responses.convert_response`。

Index-py 内置了一些处理函数用于处理常见的类型：

```python
@automatic.register(type(None))
def _none(ret: typing.Type[None]) -> typing.NoReturn:
    raise TypeError(
        "Get 'None'. Maybe you need to add a return statement to the function."
    )


@automatic.register(tuple)
@automatic.register(list)
@automatic.register(dict)
def _json(
    body, status: int = 200, headers: typing.Mapping[str, str] = None
) -> HttpResponse:
    return JSONResponse(body, status, headers)


@automatic.register(str)
@automatic.register(bytes)
def _plain_text(
    body: typing.Union[str, bytes],
    status: int = 200,
    headers: typing.Mapping[str, str] = None,
) -> HttpResponse:
    return PlainTextResponse(body, status, headers)


@automatic.register(AsyncGeneratorType)
def _send_event(
    generator: typing.AsyncGenerator[ServerSentEvent, None],
    status: int = 200,
    headers: typing.Mapping[str, str] = None,
) -> HttpResponse:
    return SendEventResponse(generator, status, headers)
```

同样的，你也可以自定义响应值的简化写法以统一项目的响应规范（哪怕有 `TypedDict`，Python 的 `Dict` 约束依旧很弱，但 dataclass 则有效得多），例如：

```python
from dataclasses import dataclass, asdict

from indexpy.http.responses import automatic, HttpResponse, JSONResponse


@dataclass
class Error:
    code: int = 0
    title: str = ""
    message: str = ""


@automatic.register(Error)
def _error_json(error: Error, status: int = 400) -> HttpResponse:
    return JSONResponse(asdict(error), status)
```

或者你想覆盖默认的 `tuple`/`list`/`dict` 所对应的 `JSONResponse`：

```python
from indexpy.responses import automatic, HttpResponse

...


@automatic.register(tuple)
@automatic.register(list)
@automatic.register(dict)
def _more_json(body: dict, status: int = 200, headers: dict = None) -> HttpResponse:
    return CustomizeJSONResponse(body, status, headers)
```

## 异常处理

### HTTPException

其参数签名是：`HTTPException(status_code: int, headers: dict = None, content: typing.Any = None)`

你可以通过抛出 `HTTPException` 来返回一个 HTTP 响应（不必担心它变成一个真正的异常抛出，Index-py 会将它变成一个普通的响应对象）。如果你没有给出一个类型为 `bytes` 或 `str` 的 `content` 值，那么它将使用 Python 标准库中的 `http.HTTPStatus(status_code).description` 作为最终结果。

```python
from indexpy.http import HTTPException


async def endpoint():
    ...
    raise HTTPException(400)
    ...
```

有时候也许你想返回更多的信息，可以像使用 `HttpResponse` 一样为它传递 `content`、`headers` 参数来控制最终实际的响应对象。下面是一个简单的例子。

```python
from indexpy.http import HTTPException


async def endpoint():
    ...
    raise HTTPException(405, headers={"Allow": "HEAD, GET, POST"})
    ...
```

### 自定义异常处理

对于一些故意抛出的异常，Index-py 提供了方法进行统一处理。

你可以捕捉指定的 HTTP 状态码，那么在应对包含对应 HTTP 状态码的 `HTTPException` 异常时，Index-py 会使用你定义的函数而不是默认行为。你也可以捕捉其他继承自 `Exception` 的异常，通过自定义函数，返回指定的内容给客户端。

```python
from indexpy import Index, HTTPException, HttpResponse, PlainTextResponse

app = Index()


@app.exception_handler(404)
def not_found(exc: HTTPException) -> HttpResponse:
    return PlainTextResponse("what do you want to do?", status_code=404)


@app.exception_handler(ValueError)
def value_error(exc: ValueError) -> HttpResponse:
    return PlainTextResponse("Something went wrong with the server.", status_code=500)
```

除了装饰器注册，你同样可以使用列表式的注册方式，下例与上例等价：

```python
from indexpy import Index, HTTPException, HttpResponse, PlainTextResponse


def not_found(exc: HTTPException) -> HttpResponse:
    return PlainTextResponse("what do you want to do?", status_code=404)


def value_error(exc: ValueError) -> HttpResponse:
    return PlainTextResponse("Something went wrong with the server.", status_code=500)


app = Index(exception_handlers={
    404: not_found,
    ValueError: value_error,
})
```
