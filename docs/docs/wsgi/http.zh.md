## 处理器

在下文中，用于处理 HTTP 请求的可调用对象被称为 HTTP 处理器。

### 函数处理器

使用函数处理请求是很简单的。

```python
from kui.wsgi import Kui

app = Kui()


@app.router.http("/hello")
def hello():
    return "hello"
```

`@app.router.http` 装饰器将返回原始的函数，故而可以将同一个函数注册到多个路由下。

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

你还可以使用 `required_method` 来约束函数处理器仅接受指定的请求方法。

```python
from kui.wsgi import Kui, request, required_method

app = Kui()


@app.router.http("/hello", middlewares=[required_method("POST")])
def need_post():
    return request.method
```

!!! notice
    当你使用 `required_method` 对请求方法进行约束时，`OPTIONS` 方法将会被自动处理。

!!! notice
    当你使用 `required_method` 允许 `GET` 方法时，`HEAD` 方法也会同时被允许。

### 类处理器

使用类处理多种请求十分简单。只需要继承 `HttpView` 并编写对应的方法，支持的方法有 `"get"`，`"post"`，`"put"`，`"patch"`，`"delete"`，`"head"`，`"options"`，`"trace"`。

!!! tip "允许更多请求方法"
    在继承类时覆盖类属性 `HTTP_METHOD_NAMES` 即可。

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

## 获取请求值

使用以下语句获取全局变量 `request`，它是一个代理对象，可以读写删当前请求对应的 `HttpRequest` 对象的各个属性。

```python
from kui.wsgi import request


def homepage():
    return request.url.path
```

一般来说这足以应付大部分需求，但如果你真的需要访问原始 `HttpRequest` 对象，可以使用

```python
from kui.wsgi import request_var


def endpoint():
    request = request_var.get()
    ...
```

以下是 `kui.wsgi.HttpRequest` 对象的常用属性与方法。

### Method

通过 `request.method` 可以获取到请求方法，例如 `GET`、`POST`。

### URL

通过 `request.url` 可以获取到请求路径。该属性是一个类似于字符串的对象，它公开了可以从URL中解析出的所有组件。

例如：`request.url.path`, `request.url.port`, `request.url.scheme`

### Path Parameters

`request.path_params` 是一个字典，包含所有解析出的路径参数。

### Headers

`request.headers` 是一个大小写无关的多值字典(multi-dict)。

通过 `request.headers.keys()`/`request.headers.items()` 取出来的 `key` 均为小写。

#### Accept

通过读取 `request.accepted_types` 属性你可以获取客户端接收的全部响应类型。

通过调用 `request.accepts` 函数你可以判断客户端接受什么样的响应类型。例如：`request.accepts("text/html")`。

#### Content Type

使用 `request.content_type` 获取 `Content-Type` 头。

#### Content Length

使用 `request.content_length` 获取 `Content-Length` 头。

#### Date

使用 `request.date` 获取 `Date` 头。

#### Referrer

使用 `request.referrer` 获取 `Referer` 头。

### Query Parameters

`request.query_params` 是一个多值字典(multi-dict)。

例如：`request.query_params['search']`

### Client Address

`request.client` 是一个 `namedtuple`，定义为 `namedtuple("Address", ["host", "port"])`。

获取客户端 hostname 或 IP 地址: `request.client.host`。

获取客户端在当前连接中使用的端口: `request.client.port`。

!!!notice
    元组中任何一个元素都可能为 None。这受限于服务器传递的值。

### Cookies

`request.cookies` 是一个标准字典，定义为 `Dict[str, str]`。

例如：`request.cookies.get('mycookie')`

### Body

有几种方法可以读到请求体内容：

- `request.body`：返回一个 `bytes`。

- `request.form`：将 `body` 作为表单进行解析并返回结果（多值字典）。

- `request.json`：将 `body` 作为 JSON 字符串解析并返回结果。

- `request.data()`：将 `body` 根据 `content_type` 提供的信息进行解析并返回。

你也可以使用 `for` 语法将 `body` 作为一个 `bytes` 流进行读取：

```python
def post():
    ...
    body = b''
    for chunk in request.stream():
        body += chunk
    ...
```

如果你直接使用了 `request.stream()` 去读取数据，那么请求体将不会缓存在内存中。其后任何对 `.body`/`.form`/`.json` 的调用都将抛出错误。

### Request Files

通过 `request.form` 可以解析通过 `multipart/form-data` 格式接收到的表单，包括文件。

文件将被包装为 `baize.datastructures.UploadFile` 对象，它有如下属性：

* `filename: str`: 被提交的原始文件名称 (例如 `myimage.jpg`).
* `content_type: str`: 文件类型 (MIME type / media type) (例如 `image/jpeg`).
* `headers: Headers`: `multipart/form-data` 格式里该文件字段携带的 Headers 信息。
* `file: tempfile.SpooledTemporaryFile`: 存储文件内容的临时文件（可以直接读写这个对象，但最好不要）。

`UploadFile` 还有五个方法：

* `write(data: bytes) -> None`: 写入数据到文件中。
* `read(size: int) -> bytes`: 从文件中读取数据。
* `seek(offset: int) -> None`: 文件指针跳转到指定位置。
* `save(filepath: str) -> None`: 将文件保存到磁盘中的指定路径。
* `close() -> None`: 关闭文件。

### State

某些情况下需要储存一些额外的自定义信息到 `request` 中，可以使用 `request.state` 进行存储。

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
* `max_age: int`，以秒为单位定义 Cookie 的生存期。非正整数会立即丢弃 Cookie。
* `expires: Optional[int]`，它定义 Cookie 过期之前的秒数。
* `path: str = "/"`，它指定 Cookie 将应用到的路由的子集。
* `domain: Optional[str]`，用于指定 Cookie 对其有效的域。
* `secure: bool = False`，指示仅当使用 HTTPS 协议发出请求时，才会将 Cookie 发送到服务器。
* `httponly: bool = False`，指示无法通过 Javascript 通过 `Document.cookie` 属性、`XMLHttpRequest` 或 `Request` 等 API 来访问 Cookie。
* `samesite: str = "lax"`，用于指定 Cookie 的相同网站策略。有效值为 `"lax"`，`"strict"` 和 `"none"`。

#### Delete Cookie

`HttpResponse` 也提供了 `delete_cookie` 方法指定已设置的 Cookie 过期。

签名: `HttpResponse.delete_cookie(key, path='/', domain=None, secure=False, httponly=False, samesite="lax")`

### PlainTextResponse

接受 `str` 或 `bytes` 并返回纯文本响应。

```python
from kui.wsgi import PlainTextResponse


def return_plaintext():
    return PlainTextResponse('Hello, world!')
```

### HTMLResponse

接受 `str` 或 `bytes` 并返回 HTML 响应。

```python
from kui.wsgi import HTMLResponse


def return_html():
    return HTMLResponse('<html><body><h1>Hello, world!</h1></body></html>')
```

### JSONResponse

接受一些 Python 对象并返回一个 `application/json` 编码的响应。

```python
from kui.wsgi import JSONResponse


def return_json():
    return JSONResponse({'hello': 'world'})
```

`JSONResponse` 以关键词参数的形式暴露出全部 `json.dumps` 的选项以供自定义。

### RedirectResponse

返回 HTTP 重定向。默认情况下使用 307 状态代码。

```python
from kui.wsgi import RedirectResponse


def return_redirect():
    return RedirectResponse('/')
```

### StreamResponse

接受一个生成器，流式传输响应主体。

```python
import time
from kui.wsgi import StreamResponse


def slow_numbers(minimum, maximum):
    yield b'<html><body><ul>'
    for number in range(minimum, maximum + 1):
        yield f'<li>{number}</li>'.encode()
        time.sleep(0.5)
    yield b'</ul></body></html>'


def return_stream(scope, receive, send):
    generator = slow_numbers(1, 10)
    return StreamResponse(generator, content_type='text/html')
```

### FileResponse

传输文件作为响应。

与其他响应类型相比，它采用不同的参数进行实例化：

* `filepath` - 要流式传输的文件的文件路径。
* `headers` - 与 `Response` 中的 `headers` 参数的作用相同。
* `content_type` - 文件的 MIME 媒体类型。如果未设置，则文件名或路径将用于推断媒体类型。
* `download_name` - 如果设置此参数，它将包含在响应的 `Content-Disposition` 中。
* `stat_result` - 接受一个 `os.stat_result` 对象，如果不传入则会自动使用 `os.stat(filepath)` 的结果。

`FileResponse` 将自动设置适当的 `Content-Length`、`Last-Modified` 和 `ETag` 标头。并且无需任何额外的处理即可支持[文件范围请求](https://developer.mozilla.org/zh-CN/docs/Web/HTTP/Range_requests)。

### TemplateResponse

`TemplateResponse` 是 `app.templates.TemplateResponse` 的一个快捷方式。

#### Jinja2 模板引擎

Kuí 内置了对 Jinja2 模板的支持，只要你安装了 `jinja2` 模块，就能从 `kui.wsgi.templates` 中导出 `Jinja2Templates`。以下是一个简单的使用样例，访问 "/" 它将从项目根目录下的 templates 目录寻找 homepage.html 文件进行渲染。

```python
from kui.wsgi import Kui, TemplateResponse, Jinja2Templates

app = Kui(templates=Jinja2Templates("templates"))


@app.router.http("/")
def homepage():
    return TemplateResponse("homepage.html")
```

如果你要使用某个模块下的指定文件夹中的模板文件，可以使用 `Jinja2Templates("module_name:dirname")`。

你还可以传递多个目录让 Jinja2 按照顺序依次查找，直到找到第一个可用的模板，例如：`Jinja2Templates("templates", "module_name:dirname")`。

#### 其他模板引擎

实现 `kui.wsgi.templates.BaseTemplates` 接口，即可实现自己的模板引擎类。

### SendEventResponse

通过 `SendEventResponse` 可以返回一个 [Server-sent Events](https://developer.mozilla.org/zh-CN/docs/Server-sent_events/Using_server-sent_events) 响应，这是一种 HTTP 长连接响应，可应用于服务器实时推送数据到客户端等场景。

`SendEventResponse` 除了可以接受诸如 `status_code`、`headers` 等常规参数外，还需要自行传入一个用于生成消息的生成器。传入的生成器 `yield` 的每一条消息都需要为合规的 Server-Sent Events 消息。

如下是一个每隔一秒发送一条 hello 消息、一共发送一百零一条消息的样例。

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

!!! tip "浏览器前端开发"
    通常情况下使用浏览器自带的 [EventSource](https://developer.mozilla.org/zh-CN/docs/Web/API/EventSource) 即可满足使用需求，但有时候你或许会需要在更复杂的场景中使用 Server-sent events（例如 OpenAI 提供的 ChatGPT 接口），使用 [@microsoft/fetch-event-source](https://github.com/Azure/fetch-event-source) 可以完成更复杂的功能。

### 响应的简化写法

为了方便使用，Kuí 允许自定义一些函数来处理 HTTP 处理器返回的非 `HttpResponse` 对象。它的原理是拦截响应，通过响应值的类型来自动选择处理函数，把非 `HttpResponse` 对象转换为 `HttpResponse` 对象。

!!! tip "主动转换"
    如果需要把函数的返回值转换为 `HttpResponse` 对象，可以使用 `kui.wsgi.convert_response`。

在下例中，视图函数返回一个 `dict` 对象，但客户端接收到的却是一个 JSON。这是因为 Kuí 内置了一些处理函数用于处理常见的类型：

- `dict | tuple | list`：自动转换为 `JSONResponse`
- `str | bytes`：自动转换为 `PlainTextResponse`
- `types.GeneratorType`：自动转换为 `SendEventResponse`
- `pathlib.PurePath`：自动转换为 `FileResponse`
- `baize.datastructures.URL`：自动转换为 `RedirectResponse`

```python
def get_detail():
    return {"key": "value"}
```

你还可以返回多个值来自定义 HTTP Status 和 HTTP Headers：

```python
def not_found():
    return {"message": "Not found"}, 404


def no_content():
    return "", 301, {"location": "https://kui.aber.sh"}
```

同样的，你也可以自定义响应值的简化写法以统一项目的响应规范（哪怕有 `TypedDict`，Python 的 `Dict` 约束依旧很弱，但 dataclass 则有效得多），如下例所示，当你在视图函数里返回 `Error` 对象时，它都会自动被转换为 `JSONResponse`，并且状态码默认为 `400`：

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

其等价于：

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

你也可以覆盖默认的转换方式，样例如下。

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

## 异常处理

### HTTPException

其参数签名是：`HTTPException(status_code: int, headers: dict = None, content: typing.Any = None)`

你可以通过抛出 `HTTPException` 来返回一个 HTTP 响应（不必担心它变成一个真正的异常抛出，Kuí 会将它变成一个普通的响应对象）。如果你没有给出 `content` 值，那么它将使用 Python 标准库中的 `http.HTTPStatus(status_code).description` 作为最终结果。

```python
from kui import HTTPException


def endpoint():
    ...
    raise HTTPException(400)
    ...
```

有时候也许你想返回更多的信息，可以像使用 `HttpResponse` 一样为它传递 `content`、`headers` 参数来控制最终实际的响应对象。下面是一个简单的例子。

```python
from kui import HTTPException


def endpoint():
    ...
    raise HTTPException(405, headers={"Allow": "HEAD, GET, POST"})
    ...
```

!!! tip
    如果你想在 `lambda` 函数里抛出 `HTTPException`，可以使用 `baize.exceptions.abort`。

### 自定义异常处理

对于一些故意抛出的异常，Kuí 提供了方法进行统一处理。

你可以捕捉指定的 HTTP 状态码，那么在应对包含对应 HTTP 状态码的 `HTTPException` 异常时，Kuí 会使用你定义的函数而不是默认行为。你也可以捕捉其他继承自 `Exception` 的异常，通过自定义函数，返回指定的内容给客户端。

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

除了装饰器注册，你同样可以使用列表式的注册方式，下例与上例等价：

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

## 允许跨域请求

在现代浏览器中解决跨域问题一般使用 [Cross-Origin Resource Sharing](https://developer.mozilla.org/zh-CN/docs/Web/HTTP/CORS)，在 Kuí 使用如下代码即可快速配置 API 允许跨域。

```python
from kui.wsgi import Routes, allow_cors

routes = Routes(..., http_middlewares=[allow_cors()])
```

`allow_cors` 有如下参数：

- `allow_origins: Iterable[Pattern]`：允许的 Origin。需要 `re.compile` 预编译后的 `Pattern` 对象；默认值为 `(re.compile(".*"), )`
- `allow_methods: Iterable[str]`：允许的请求方法。默认值为 `("GET"，"POST"，"PUT"，"PATCH"，"DELETE"，"HEAD"，"OPTIONS"，"TRACE")`。
- `allow_headers: Iterable[str]`：允许的请求头。对应 [`Access-Control-Allow-Headers`](https://developer.mozilla.org/zh-CN/docs/Web/HTTP/Headers/Access-Control-Allow-Headers)。
- `expose_headers: Iterable[str]`：能在响应中列出的请求头。对应 [`Access-Control-Expose-Headers`](https://developer.mozilla.org/zh-CN/docs/Web/HTTP/Headers/Access-Control-Expose-Headers)。
- `allow_credentials: bool`：为真时则允许跨域请求携带 Cookies，反之不允许。默认为 `False`。
- `max_age: int`：预请求的缓存时间。默认为 `600` 秒。

如果你需要在全局开启 CORS，可以给 `Kui` 传入 `cors_config` 参数。它是一个字典，键值与 `allow_cors` 参数相同。

```python
from kui.wsgi import Kui

app = Kui(cors_config={})
```
