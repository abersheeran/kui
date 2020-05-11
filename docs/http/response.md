## 响应类型

对于任何正常处理的 HTTP 请求都必须返回一个 `indexpy.http.responses.Response` 对象或者是它的子类对象。

在 `index.http.repsonses` 里内置的可用对象如下：

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
from indexpy.http import HTTPView
from indexpy.http.responses import TemplateResponse


class HTTP(HTTPView):
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
from indexpy.http.responses import automatic


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
from indexpy.http import HTTPView


class HTTP(HTTPView):

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
