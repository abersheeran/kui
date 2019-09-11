## Response

对于任何正常处理的 HTTP 请求都必须返回一个 `index.responses.Response` 对象或者是它的子类对象。

在 `index.repsonses` 里内置的可用对象如下：

* [Response](https://www.starlette.io/responses/#response)
* [HTMLResponse](https://www.starlette.io/responses/#htmlresponse)
* [PlainTextResponse](https://www.starlette.io/responses/#plaintextresponse)
* [JSONResponse](https://www.starlette.io/responses/#jsonresponse)
* [RedirectResponse](https://www.starlette.io/responses/#redirectresponse)
* [StreamingResponse](https://www.starlette.io/responses/#streamingresponse)
* [FileResponse](https://www.starlette.io/responses/#fileresponse)
* [TemplateResponse](https://www.starlette.io/templates/#testing-template-responses)

## 自定义返回类型

为了方便使用，Index 允许自定义一些函数来处理 `HTTP` 内的处理方法返回的非 `Response` 对象。

在项目根目录定义文件 `responses.py`，在其中编写自己的处理函数。

以下是一个处理 `dict` 类型的返回值的例子。

* 注意：你也可以不使用 `typeassert` 装饰器和 type hint，这并非强制的，但推荐使用，它能在编写/调试时让你更方便。

```python
from index.types import typeassert
from index.responses import register_type

from starlette.background import BackgroundTask


@register_type(dict)
@typeassert
def json_type(
    body: dict,
    status: int = 200,
    headers: dict = None,
    background: BackgroundTask = None
) -> Response:

    return JSONResponse(
        body,
        status,
        headers,
        background=background
    )
```

再接着看下面这个类

```python
from index.view import View


class HTTP(View):

    async def get(self):
        return {"message": "some error in server"}, 500, {"server": "index.py"}
```

当一个 HTTP GET 请求被该类处理后，Index 会判断返回值的第一个值的类型，如果不是 `Response` 或者其子类对象时，则从已经注册过的类型中查找对应的函数进行处理，查找到对应函数后，将所有的返回值作为位置参数（position parameter）传递给函数，而处理函数必须返回一个 `Response` 或者其子类对象。

### 内置的处理函数

Index 内置了两个处理函数，它们的定义如下：

```python
@register_type(dict)
@typeassert
def json_type(
    body: dict,
    status: int = 200,
    headers: dict = None,
    background: BackgroundTask = None
) -> Response:

    return JSONResponse(
        body,
        status,
        headers,
        background=background
    )
```

```python
@register_type(str)
@typeassert
def text_type(
    body: str,
    status: int = 200,
    headers: dict = None,
    background: BackgroundTask = None
) -> Response:

    return PlainTextResponse(
        body,
        status,
        headers,
        background=background
    )
```
