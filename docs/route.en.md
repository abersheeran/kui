The router of Index-py is based on [Radix Tree](https://en.wikipedia.org/wiki/Radix_tree)。

## Simple Usage

### Using Decorators

Similar to web frameworks like bottle and flask，Index-py support route registration via decorator. In the following example, `name` is the name of route, and it will be used in searching route by name.

```python
from indexpy import Index

app = Index()


@app.router.http("/hello", name="hello")
async def hello():
    ...


@app.router.websocket("/hello", name="hello_ws")
async def hello_ws():
    ...
```

!!! tip ""
    If `name` is not specified, Index-py will use the `__name__` property of the callable object by default. 

!!! notice ""
    If `name` is set to `None`, searching this router by name won't work.

### Route Object

In fact, the decorator route registration method is a shortcut of the following method

```python
from indexpy import Index
from indexpy.routing import HttpRoute, SocketRoute

app = Index()


async def hello():
    return "hello world"


async def hello_ws():
    ...


(
    app.router
    << HttpRoute("/hello", hello, name="hello")
    << SocketRoute("/hello", hello_ws, name="hello_ws")
)
```

Index-py has two route objects, corresponding to Http and WebSocket methods.

```python
# Http
HttpRoute(path: str, endpoint: Any, name: Optional[str] = "")

# WebSocket
SocketRoute(path: str, endpoint: Any, name: Optional[str] = "")
```

- `path` specify the string router can match

- `endpoint` specify the callable object

- `name` specify the route's name. When `name` is `None`, the route will have no name; When `name` is `""`, Index-py will use `endpoint.__name__`.

#### Preprocessing

Index-py will register a decorator to the endpoint to process some parameters' auto-validation and injection.

#### Middlewares

You can add middlewares to route objects, and these will affect the endpoint. Versus using decorators on endpoint directly, using middlewares will affect on preprocessed endpoint.

!!! tip ""
    You can catch potentional parameters validation exception in registered middlewares. 

!!! notice ""
    In this document, decorators registered like this is called `middlwares`. 

```python
HttpRoute(...) @ decorator
```

像注册普通的装饰器一样，你可以注册多个；执行顺序也一样，由远到近的执行。

```python
HttpRoute(...) @ decorator1 @ decorator2 @ decorator3
```

并且，你同样可以在使用装饰器进行路由注册时注册中间件，如下所示，其执行顺序同样是由右到左。

```python
@app.router.http("/path", middlewares=[decorator1, decorator2, decorator3])
async def path(): ...
```

### 限定请求方法

!!! notice ""
    指定支持 GET 方法时，HEAD 将被自动允许。

!!! tip ""
    限定了请求方法后，OPTIONS 的请求将被自动处理。反之，你需要自行处理 OPTIONS 方法。

在使用装饰器注册时可以直接限定该路由能够接受的请求方法，目前仅支持以下五种 HTTP 方法的限定。如果你没有指定，则默认允许所有请求方法。

```python
from indexpy import Index

app = Index()


@app.router.http.get("/get")
async def need_get():
    ...


@app.router.http.post("/post")
async def need_post():
    ...


@app.router.http.put("/put")
async def need_put():
    ...


@app.router.http.patch("/patch")
async def need_patch():
    ...


@app.router.http.delete("/delete")
async def need_delete():
    ...
```

如上代码是在内部使用了 `required_method` 装饰器来达到限定请求方法的目的，你也可以选择手动注册装饰器，这将能限定更多种类的请求。代码样例如下：

```python
from indexpy import Index, required_method

app = Index()


@app.router.http("/get")
@required_method("GET")
async def need_get():
    ...


@app.router.http("/connect")
@required_method("CONNECT")
async def need_connect():
    ...
```


### 列表式注册

Index-py 同样支持类似于 Django 的列表式写法：

```python
from indexpy import Index
from indexpy.routing import HttpRoute, SocketRoute


async def hello():
    return "hello world"


async def hello_ws():
    ...


app = Index(routes=[
    HttpRoute("/hello", hello, name="hello"),
    SocketRoute("/hello", hello_ws, name="hello_ws"),
])
```

### 路径参数

使用 `{name:type}` 可以标注路径参数，目前支持的类型有 `str`、`int`、`decimal`、`date`、`uuid` 和 `path`。

!!! tip ""
    如果路径参数的类型为 `str`，可以忽略掉 `:str`，直接使用 `{name}`。

!!! notice ""
    `str` 不能匹配到 `/`，如果需要匹配 `/` 请使用 `path`。

!!! notice ""
    `path` 是极为特殊的参数类型，它只能出现在路径的最后，并且能匹配到所有的字符。

```python
from indexpy import Index, request

app = Index()


@app.router.http("/{username:str}")
async def what_is_your_name():
    return request.path_params["username"]
```

### 反向查找

某些情况下，需要由路由名称反向生成对应的 URL 值，可以使用 `app.router.url_for`。

```python
from indexpy import Index, request

app = Index()


@app.router.http("/hello", name="hello")
@app.router.http("/hello/{name}", name="hello-with-name")
async def hello():
    return f"hello {request.path_params.get('name')}"


assert app.router.url_for("hello") == "/hello"
assert app.router.url_for("hello-with-name", {"name": "Aber"}) == "/hello/Aber"
```

!!! tip ""
    反向查找中，`websocket` 与 `http` 是互相独立的。通过 `protocol` 参数可以选择查找的路由，默认为 `http`。

## 路由分组

当需要把某一些路由归为一组时，可使用 `Routes` 对象。

`Routes` 对象拥有 `.http` 和 `.websocket` 方法允许你使用装饰器方式注册路由，使用方法与 `app.router` 相同。

`Routes` 也同样允许你使用类似于 Django 一样的路由申明方式，示例如下。

```python
from indexpy.routing import Routes, HttpRoute


async def hello(request):
    return "hello world"


routes = Routes(
    HttpRoute("/hello", hello),
)
```

使用 `<<` 运算符即可注册 `Routes` 中所有路由给 `app.router`，并且这一运算的返回结果是 `app.router`，这意味着你可以进行链式调用。

```python
from .app1.urls import routes as app1_routes
from .app2.urls import routes as app2_routes

app.router << app1_routes << app2_routes
```

当然，你也可以直接在初始化 `Index` 对象时传入。

```python
from indexpy import Index

from .app1.urls import routes as app1_routes

app = Index(routes=app1_routes)
```

### 路由组合

`Routes` 可以轻松和其他 `Routes` 组合起来。

```python
from .app1.urls import routes as app1_routes

routes = Routes(...) << app1_routes
```

并且 `<<` 的结果是运算左侧的 `Routes` 对象，这意味着你可以链式调用它，如下所示。

```python
from .app1.urls import routes as app1_routes
from .app2.urls import routes as app2_routes


Routes() << app1_routes << app2_routes
```

你也可以合并两个 `Routes` 成为一个新的 `Routes` 对象，而不是将其中一个合并到另一个里。

```python
from .app1.urls import routes as app1_routes
from .app2.urls import routes as app2_routes


new_routes = app1_routes + app2_routes
```

### 名称空间

你可以为 `Routes` 设置 `namespace` 参数，这将在 `Routes` 对象中包含的每个路由名称（如果有的话）前加上 `namespace:`，以此来避免不同名称空间内的路由名称冲突。

```python
routes = Routes(..., namespace="namespace")
```

!!! notice ""

    在使用 `app.router.url_for` 时不要忘记加上路由所在的名称空间前缀。

### 中间件注册

通过 `Routes` 你可以为整组路由注册一个或多个中间件。以下为简单的样例：

```python
def one_http_middleware(endpoint):
    async def wrapper():
        return await endpoint()
    return wrapper


def one_socket_middleware(endpoint):
    async def wrapper():
        return await endpoint()
    return wrapper


routes = Routes(
    ...,
    http_middlewares=[one_http_middleware],
    socket_middlewares=[one_socket_middleware],
)
```

当然，你同样可以使用装饰器来注册中间件，与上例的结果没有什么不同。

```python
routes = Routes(...)


@routes.http_middleware
def one_http_middleware(endpoint):
    async def wrapper():
        return await endpoint()
    return wrapper


@routes.socket_middleware
def one_socket_middleware(endpoint):
    async def wrapper():
        return await endpoint()
    return wrapper
```

### 公共前缀

有时候某一组的路由我们希望放到同一个前缀下，如下两段代码的结果是相同的。

```python
routes = "/auth" // Routes(
    HttpRoute("/login", ...),
    HttpRoute("/register", ...),
)
```

```python
routes = Routes(
    HttpRoute("/auth/login", ...),
    HttpRoute("/auth/register", ...),
)
```

!!! Warning "注意事项"

    在使用 `routes = "prefix" // Routes(......)` 之后再调用 `@routes.http` 等方法注册路由时，并不会给后续的路由自动加上 `"prefix"` 前缀。你应当在一个路由分组内所有路由注册完成之后，再进行 `"prefix" // routes` 运算。

## 路由拓展

通过构建路由对象的序列（`Sequence[BaseRoute]`）可以编写自己喜爱的路由注册方式，在最终都会合并进 Radix Tree 里。

### FileRoutes

```
from indexpy.routing.extensions import FileRoutes
```

!!! notice ""
    这也是 Index.py 此项目的命名来源之一。

`FileRoutes` 是一个特殊的路由序列，它允许你将某一个 `module` 下所有的 `.py` 文件一一对应到其相对路径相同的路由。

#### 中间件定义

`__init__.py` 中名为 `HTTPMiddleware` 的对象将被作为 HTTP 中间件、`SocketMiddleware` 将被作为 WebSocket 中间件，并作用于同目录下所有的路由。

#### 处理器定义

除了 `__init__.py` 文件以外的 `.py` 文件中，名为 `HTTP` 的对象（任何可调用对象均可，函数、类等）将被视为 HTTP 处理器，名为 `Socket` 的对象（任何可调用对象均可，函数、类等）将被视为 WebSocket 处理器。

#### 路由名称

在文件中定义名称为 `name` 的字符串将作为该文件对应的路由名称。

`FileRoutes` 同样拥有 `namespace` 参数，并且拥有同样的作用。

#### 映射规则

`module/filename.py` 文件将对应路由 `/filename`，`module/dirname/filename.py` 将对应 `/dirname/filename`，以此类推。

文件映射有一个特殊规则：`module/**/index.py` 将负责处理 `/**/` 路径的内容。

!!! tip ""
    你可以将文件名或文件夹名修改为 `module/{name}.py` 以此接受路径参数。

可以为 `FileRoutes` 设置 `suffix` 参数，给每个路由加上后缀，譬如 `suffix=".php"` 这将使路径看起来很像 PHP 😀。

### MultimethodRoutes

```
from indexpy.routing.extensions import MultimethodRoutes
```

`MultimethodRoutes` 是一个特殊的路由序列，它允许你使用如下方式注册路由，在不显式使用类的情况下拆分同一个 PATH 下的不同方法到多个函数中。除此之外，均与 `Routes` 相同。

```python
from indexpy import Index
from indexpy.routing.extensions import MultimethodRoutes

routes = MultimethodRoutes()


@routes.http.get("/user")
async def list_user():
    pass


@routes.http.post("/user")
async def create_user():
    pass


@routes.http.delete("/user")
async def delete_user():
    pass
```
