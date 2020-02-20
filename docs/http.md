## 处理 HTTP 请求

在`views`里创建任意合法名称的`.py`文件，并在其中创建名为 `HTTP` 的类，即可使此文件能够处理对应其相对于 `views` 的路径的 HTTP 请求。

但较为特殊的是名为 `index.py` 的文件，它能够处理以 `/` 作为最后一个字符的 URI。

!!! tip
    由于 Python 规定，模块名称必须由字母、数字与下划线组成，但这种 URI 不友好，所以 Index 会将 URI 中的 `_` 全部替换成 `-` 并做 301 跳转，你可以通过设置 [ALLOW_UNDERLINE](/config/#allow_underline) 为真去关闭此功能。

一些例子|文件相对路径|文件能处理的URI
---|---|---
|views/index.py|/
|views/about.py|/about
|views/api/create_article.py|/api/create-article
|views/article/index.py|/article/

`HTTP` 的类应从 `indexpy.view.View` 继承而来，你可以定义如下方法去处理对应的 HTTP 请求。

- get
- post
- put
- patch
- delete
- head
- options
- trace

这些函数默认不接受任何参数，但可以使用 `self.request` 去获取此次请求的一些信息，它是一个 `starlette.requests.Request` 对象。详细的属性或方法请查看 [starlette 文档](https://www.starlette.io/requests/#request)。

!!! notice
    注意：这些被用于实际处理 HTTP 请求的函数，无论你以何种方式定义，都会在加载时被改造成异步函数，但为了减少不必要的损耗，尽量使用 `async def` 去定义它们。

## 编写中间件

在 `views` 中任意 `__init__.py` 中定义名为 `Middleware` 的类, 它将能处理所有通过该路径的 HTTP 请求。

譬如在 `views/__init__.py` 中定义的中间件，能处理所有 URI 的 HTTP 请求；在 `views/api/__init__.py` 则只能处理 URI 为 `/api/*` 的请求。

`Middleware` 需要继承 `indexpy.middleware.MiddlewareMixin`，有以下两个方法可以重写。

1. `process_request(request)`

    此方法在请求被层层传递时调用，可用于修改 `request` 对象以供后续处理使用。必须返回 `None`，否则返回值将作为最终结果并直接终止此次请求。

2. `process_response(request, response)`

    此方法在请求被正常处理、已经返回响应对象后调用，它必须返回一个可用的响应对象（一般来说直接返回 `response` 即可）。

!!! notice
    以上函数无论你以何种方式定义，都会在加载时被改造成异步函数，但为了减少不必要的损耗，尽量使用 `async def` 去定义它们。

### 子中间件

很多时候，对于同一个父 URI，需要有多个中间件去处理。通过指定 `Middleware` 中的 `ChildMiddlwares` 属性，可以为中间件指定子中间件。执行时会先执行父中间件，再执行子中间件。

!!! notice
    子中间件的执行顺序是从右到左。

```python
from indexpy.middleware import MiddlewareMixin
from indexpy.config import logger


class ExampleChildMiddleware(MiddlewareMixin):

    async def process_request(self, request):
        logger.info("example base middleware request")

    async def process_response(self, request, response):
        logger.info("example base middleware response")
        return response


class Middleware(MiddlewareMixin):

    ChildMiddlwares = (ExampleChildMiddleware, )

    async def process_request(self, request):
        logger.info("enter first process request")

    async def process_response(self, request, response):
        logger.info("enter last process response")
        return response
```

## 响应类型

对于任何正常处理的 HTTP 请求都必须返回一个 `index.responses.Response` 对象或者是它的子类对象。

在 `index.repsonses` 里内置的可用对象如下：

* [Response](https://www.starlette.io/responses/#response)
* [HTMLResponse](https://www.starlette.io/responses/#htmlresponse)
* [PlainTextResponse](https://www.starlette.io/responses/#plaintextresponse)
* [JSONResponse](https://www.starlette.io/responses/#jsonresponse)
* [RedirectResponse](https://www.starlette.io/responses/#redirectresponse)
* [StreamingResponse](https://www.starlette.io/responses/#streamingresponse)
* [FileResponse](https://www.starlette.io/responses/#fileresponse)
* TemplateResponse
* YAMLResponse

### TemplateResponse

Index 提供了使用 Jinja2 的方法。如下代码将会自动在项目下的 `templates` 目录里寻找对应的模板进行渲染。

```python
from indexpy.view import View
from indexpy.responses import TemplateResponse


class HTTP(View):
    def get(self):
        return TemplateResponse("chat.html", {"request": self.request})
```

### YAMLResponse

由于 YAML 与 JSON 的等价性，YAMLResponse 与 JSONResponse 的使用方法相同。

唯一不同的是，一个返回 YAML 格式，一个返回 JSON 格式。

### 自定义返回类型

为了方便使用，Index 允许自定义一些函数来处理 `HTTP` 内的处理方法返回的非 `Response` 对象。

在项目根目录定义文件 `responses.py`，在其中编写自己的处理函数。

以下是一个处理 `dict` 类型的返回值的例子。

```python
from indexpy.responses import automatic


@automatic.register(dict)
def _automatic(
    body: typing.Dict,
    status: int = 200,
    headers: dict = None
) -> Response:

    return JSONResponse(body, status, headers)
```

再接着看下面这个类

```python
from indexpy.view import View


class HTTP(View):

    async def get(self):
        return {"message": "some error in server"}, 500, {"server": "index.py"}
```

当一个 HTTP GET 请求被该类处理后，Index 会判断返回值的第一个值的类型，如果不是 `Response` 或者其子类对象时，则从已经注册过的类型中查找对应的函数进行处理，查找到对应函数后，将所有的返回值作为位置参数（position parameter）传递给函数，而处理函数必须返回一个 `Response` 或者其子类对象。

### 内置的处理函数

Index 内置了两个处理函数用于处理三种类型：

```python
@automatic.register(dict)
def _automatic(body: typing.Dict, status: int = 200, headers: dict = None) -> Response:
    return JSONResponse(body, status, headers)


@automatic.register(str)
@automatic.register(bytes)
def _automatic(
    body: typing.Union[str, bytes], status: int = 200, headers: dict = None
) -> Response:
    return PlainTextResponse(body, status, headers)
```
