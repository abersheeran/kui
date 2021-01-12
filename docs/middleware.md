在了解 Index-py 的中间件注册方式之前，先看看本框架的中间件设计思路——每个中间件都是给 `endpoint` 的装饰器。事实上，Index-py 的中间都会在路由展开时以装饰器相同的方式层层包裹最终的 `endpoint`。如果你愿意手动为每个 `endpoint` 加上装饰器，那么你也可以不需要使用 Index-py 中间件。

## HTTP 中间件

### 基于函数的中间件

编写一个 HTTP 中间件十分简单，就像编写一个装饰器函数一样。

第一层函数只有一个参数，就是被包裹的可调用对象。第二层函数仅接受一个参数 `requesst`，函数返回值将作为此次请求的响应结果。

```python
def middleware(endpoint):
    async def wrapper(request):
        ...
        response = await endpoint(request)
        ...
        return response
    return wrapper
```

!!! tip
    `endpoint` 是实际处理 HTTP 请求的可调用对象

### 基于类的中间件

基于类的中间件可以继承 `indexpy.http.MiddlewareMixin`，有以下三个方法可以重写。

- `process_request(request: Request)`

    此方法在请求被层层传递时调用，可用于修改 `request` 对象以供后续处理使用。必须返回 `None`，否则返回值将作为最终结果并直接终止此次请求。

- `process_response(request: Request, response: Response)`

    此方法在请求被正常处理、已经返回响应对象后调用，它必须返回一个可用的响应对象（一般来说直接返回 `response` 即可）。

- `process_exception(request: Request, exception: Exception)`

    此方法在中间件之后的调用链路上出现异常时被调用。当其返回值为 `None` 时，异常会被原样抛出，否则其返回值将作为此次请求的响应值被返回。

!!! notice
    以上函数无论你以何种方式定义，都会在加载时被改造成异步函数，但为了减少不必要的损耗，尽量使用 `async def` 去定义它们——除非在其中使用了含有阻塞 IO 的其他函数，例如 Django ORM, PonyORM 等。

通过指定 `Middleware` 中的 `mounts` 属性，可以为中间件指定子中间件。执行时会先执行父中间件，再执行子中间件。

!!! notice
    子中间件的执行顺序是从左到右。

```python
from indexpy.http import MiddlewareMixin


class ExampleChildMiddleware(MiddlewareMixin):
    async def process_request(self, request):
        print("enter first process request")

    async def process_response(self, request, response):
        print("enter last process response")
        return response


class Middleware(MiddlewareMixin):
    mounts = (ExampleChildMiddleware,)

    async def process_request(self, request):
        print("example base middleware request")

    async def process_response(self, request, response):
        print("example base middleware response")
        return response
```

## WebSocket 中间件

### 基于函数的中间件

编写一个 WebSocket 中间件与编写一个 HTTP 中间件很相似，不同的是 `websocket` 对应的 `endpoint` 对象不会有返回值。中间件的第二层函数也不需要返回结果，任何返回结果都是无效的。

```python
def middleware(endpoint):
    async def wrapper(websocket):
        ...
        await endpoint(websocket)
        ...
    return wrapper
```

!!! tip
    `endpoint` 是实际处理 WebSocket 请求的可调用对象

### 基于类的中间件

基于类的中间件可以继承 `indexpy.websocket.MiddlewareMixin`，有以下两个方法可以重写。

- `before_accept(websocket: WebSocket) -> None`

    此方法在 websocket 连接被接受前调用。

- `after_close(websocket: WebSocket) -> None`

    此方法在 websocket 连接被关闭后调用。

同样的，`indexpy.websocket.MiddlewareMixin` 也有 `mounts` 属性用于挂在子中间件。

## ASGI 中间件

在 Index-py 中，定义并使用 ASGI 中间件的方式有两种，一种是与 Starlette 相同的注册方式，将 ASGI 中间件注册给 Index-py 对象；另一种是将 ASGI 中间件注册给指定的 [`ASGIRoute`](./route.md#asgiroute)。这两种 ASGI 中间件的定义方法不同，使用方法不同，作用范围也不同。

### 附加给 Index-py 对象的 ASGI 中间件

就像[ Starlette 文档](https://www.starlette.io/middleware/)里的中间件一样，这一类的中间件定义，它的 `__init__` 签名必须为 `(self, app: ASGIApp, *args: Any, **kwargs: Any)`，`__call__` 必须是一个标准的 ASGI 接口。注册方式类似于如下代码：

```python
from indexpy import Index
from starlette.middleware.gzip import GZipMiddleware

app = Index()
app.add_middleware(GZipMiddleware, minimum_size=1000)
```

### 附加到路由的 ASGI 中间件

这种方式就如同最上面所讲的，使用装饰器相同的编写方式。以下为一个简单的定义样例，注册方式请参考 [Routes 章节](./route.md#_10)。

```python
from indexpy.types import ASGIApp

def middleware(app: ASGIApp):
    async def wrapper(scope, receive, send):
        ...
        await app(scope, receive, send)
        ...
    return wrapper
```
