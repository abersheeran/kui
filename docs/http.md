## 获取请求值

以下是 `indexpy.http.request.Request` 对象的常用属性与方法。

### Method

通过 `request.method` 可以获取到请求方法，例如 `get`/`post` 等。

### URL

通过 `request.url` 可以获取到请求路径。该属性是一个类似于字符串的对象，它公开了可以从URL中解析出的所有组件。

例如：`request.url.path`, `request.url.port`, `request.url.scheme`

### Headers

`request.headers` 是一个大小写无关的多值字典(multi-dict)。但通过 `request.headers.keys()`/`request.headers.items()` 取出来的 `key` 均为小写。

### Query Parameters

`request.query_params` 是一个不可变的多值字典(multi-dict)。

例如：`request.query_params['search']`

### Client Address

`request.client` 是一个 `namedtuple`，定义为 `namedtuple("Address", ["host", "port"])`。

获取客户端 hostname 或 IP 地址: `request.client.host`。

获取客户端在当前连接中使用的端口: `request.client.port`。

!!!notice
    元组中任何一个元素都可能为 None。这受限于 ASGI 服务器传递的值。

### Cookies

`request.cookies` 是一个标准字典，定义为 `Dict[str, str]`。

例如：`request.cookies.get('mycookie')`

!!!notice
    你没办法从`request.cookies`里读取到无效的 cookie (RFC2109)

### Body

有几种方法可以读到请求体内容：

- `await request.body()`：返回一个 `bytes`。

- `await request.form()`：将 `body` 作为表单进行解析并返回结果（多值字典）。

- `await request.json()`：将 `body` 作为 JSON 字符串解析并返回结果。

你也可以使用 `async for` 语法将 `body` 作为一个 `bytes` 流进行读取：

```python
async def post(self):
    ...
    body = b''
    async for chunk in self.request.stream():
        body += chunk
    ...
```

如果你直接使用了 `request.stream()` 去读取数据，那么请求体将不会缓存在内存中。其后任何对 `.body()`/`.form()`/`.json()` 的调用都将抛出错误。

在某些情况下，例如长轮询或流式响应，你可能需要确定客户端是否已断开连接。可以使用 `disconnected = await request.is_disconnected()` 确定此状态。

### Request Files

通过 `await request.form()` 可以解析通过 `multipart/form-data` 格式接收到的表单，包括文件。

文件将被包装为 `starlette.datastructures.UploadFile` 对象，它有如下属性：

* `filename: str`: 被提交的原始文件名称 (例如 `myimage.jpg`).
* `content_type: str`: 文件类型 (MIME type / media type) (例如 `image/jpeg`).
* `file: tempfile.SpooledTemporaryFile`: 存储文件内容的临时文件（可以直接读写这个对象，但最好不要）。

`UploadFile` 还有四个异步方法（当文件在内存中时将直接进行操作，在磁盘时将使用多线程包裹原始文件的操作从而得到异步能力 [starlette#933](https://github.com/encode/starlette/pull/933)）。

* `async write(data: Union[str, bytes])`: 写入数据到文件中。
* `async read(size: int)`: 从文件中读取数据。
* `async seek(offset: int)`: 文件指针跳转到指定位置。
* `async close()`: 关闭文件。

下面是一个读取原始文件名称和内容的例子：

```python
form = await request.form()
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

对于任何正常处理的 HTTP 请求都必须返回一个 `indexpy.http.responses.Response` 对象或者是它的子类对象。

在 `index.http.repsonses` 里内置的可用对象如下：

### [Response](https://www.starlette.io/responses/#response)

### [HTMLResponse](https://www.starlette.io/responses/#htmlresponse)

### [PlainTextResponse](https://www.starlette.io/responses/#plaintextresponse)

### [JSONResponse](https://www.starlette.io/responses/#jsonresponse)

### [RedirectResponse](https://www.starlette.io/responses/#redirectresponse)

### [StreamingResponse](https://www.starlette.io/responses/#streamingresponse)

### [FileResponse](https://www.starlette.io/responses/#fileresponse)

### TemplateResponse

Index 提供了使用 Jinja2 的方法。如下代码将会自动在项目下寻找对应的模板进行渲染。（寻找路径由 Index 的 `templates` 参数进行配置）

```python
from indexpy.http import HTTPView
from indexpy.http.responses import TemplateResponse


class HTTP(HTTPView):
    def get(self):
        return TemplateResponse("chat.html", {"request": self.request})
```

`TemplateResponse` 使用的 `jinja2.Environment` 来自于 `Index().jinja_env`，通过更改、覆盖等方式，你可以自由的控制 `TemplateResponse`。

例子：

```python
from datetime import datetime
from indexpy import Index

app = Index()
app.jinja_env.globals["now"] = datetime.now
```

### YAMLResponse

YAMLResponse 与 JSONResponse 的使用方法相同。

唯一不同的是，一个返回 YAML 格式，一个返回 JSON 格式。

### 响应的简化写法

为了方便使用，Index 允许自定义一些函数来处理 `HTTP` 内返回的非 `Response` 对象。它的原理是拦截响应，通过响应值的类型来自动选择处理函数，把非 `Response` 对象转换为 `Response` 对象。

Index 内置了三个处理函数用于处理六种类型：

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
    body: typing.Tuple[tuple, list, dict],
    status: int = 200,
    headers: dict = None
) -> Response:
    return JSONResponse(body, status, headers)


@automatic.register(str)
@automatic.register(bytes)
def _plain_text(
    body: typing.Union[str, bytes], status: int = 200, headers: dict = None
) -> Response:
    return PlainTextResponse(body, status, headers)
```

正是有了这些内置处理函数，下面这段代码将被正确解析为一个 JSON 响应。

```python
from indexpy.http import HTTPView


class HTTP(HTTPView):

    def get(self):
        return {"key": "value"}
```

同样的，你也可以自定义响应值的简化写法以统一项目的响应规范（哪怕有 `TypedDict`，Python 的 `Dict` 约束依旧很弱，但 dataclass 则有效得多），例如：

```python
from dataclasses import dataclass, asdict

from indexpy.http.responses import automatic, Response, JSONResponse


@dataclass
class Error:
    code: int = 0
    title: str = ""
    message: str = ""


@automatic.register(Error)
def _error_json(error: Error, status: int = 400) -> Response:
    return JSONResponse(asdict(error), status)
```

### 默认响应

当你需要返回一个 HTTP 状态码以及其默认的描述时，可以使用

```python
raise indexpy.http.HTTPException(CODE)
```

其好处在于你可以通过[自定义异常处理](#_8)来捕捉并自定义它们。

例如：网站需要有统一的 404 页面。

## 自定义异常处理

对于一些故意抛出的异常，Index 提供了方法进行统一处理。

以下为样例：

```python
from indexpy import Index
from indexpy.types import Request, Response
from indexpy.http.responses import PlainTextResponse
from indexpy.http import HTTPException

app = Index()


@app.exception_handler(404)
def not_found(request: Request, exc: HTTPException) -> Response:
    return PlainTextResponse("what do you want to do?", status_code=404)


@app.exception_handler(ValueError)
def value_error(request: Request, exc: ValueError) -> Response:
    return PlainTextResponse("Something went wrong with the server.", status_code=500)
```

!!!notice
    如果是捕捉 HTTP 状态码，则会捕捉 `indexpy.http.HTTPException`。

!!!tip
    在此可以捕捉包括挂载到 Index 中的其他 app 的异常。而中间件中仅能处理通过中间件的异常。
