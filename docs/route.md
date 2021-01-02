Index 的路由基于 [Radix Tree](https://en.wikipedia.org/wiki/Radix_tree)。

## 基本用法

### 装饰器注册

与 bottle/flask 之类的框架一样，Index 支持使用装饰器注册路由。下面的例子里，`name` 是路由名称，这在反向查找路由时会起到作用。

```python
from indexpy import Index

app = Index()


@app.router.http("/hello", name="hello", method="get")
async def hello(request):
    return "hello world"


@app.router.websocket("/hello", name="hello_ws")
async def hello_ws(websocket):
    ...


@app.router.asgi(
    "/static{filepath:path}",
    name="static",
    type=("http",),
    root_path="/static"
)
async def static(scope, receive, send):
    ...
```

!!! tip
    如果 `name` 没有被指定，则会默认使用被注册的可调用对象的 `__name__` 属性。

!!! notice
    如果指定路由的 `name` 为 `None`，则无法通过 `name` 查找到该路由。

### 路由对象

事实上，装饰器路由申明方式是如下方法的快捷方式

```python
from indexpy import Index
from indexpy.routing import HttpRoute, SocketRoute, ASGIRoute

app = Index()


async def hello(request):
    return "hello world"


async def hello_ws(websocket):
    ...


async def static(scope, receive, send):
    ...


app.router.append(HttpRoute("/hello", hello, name="hello", method="get"))
app.router.append(SocketRoute("/hello", hello_ws, name="hello_ws"))
app.router.append(
    ASGIRoute(
        "/static{filepath:path}",
        static,
        name="static",
        type=("http",),
        root_path="/static",
    )
)
```

#### HttpRoute

```python
HttpRoute(path: str, endpoint: Any, name: Optional[str] = "", method: str = "")
```

- `name` 用于为路由指定名称，`name` 为 `None` 时，此路由将没有名称；`name` 为 `""` 时，将自动读取 `endpoint.__name__` 作为路由名称。

- `method` 用于为 `endpoint` 指定一个允许的 HTTP Method，必须是小写的有效的 HTTP Method 名称。但仅在 `endpoint` 是函数时需要指定此参数。

#### SocketRoute

```python
SocketRoute(path: str, endpoint: Any, name: Optional[str] = "")
```

所有参数的作用与 `HttpRoute` 相同。

#### ASGIRoute

```python
ASGIRoute(path: str, endpoint: Any, name: Optional[str] = "", type: typing.Container[Literal["http", "websocket"]] = ("http", "websocket"), root_path: str = "")
```

- `type` 用于为此路由指定允许接受的请求类型，默认为 `http`、`websocket` 两种。

- `root_path` 用于挂载此路由的应用到指定的 `root_path` 下。

### 列表式注册

Index 同样支持类似于 Django 的列表式写法：

```python
from indexpy import Index
from indexpy.routing import HttpRoute, SocketRoute

app = Index()


async def hello(request):
    return "hello world"


async def hello_ws(websocket):
    ...


app.router.extend([
    HttpRoute("/hello", hello, name="hello", method="get"),
    SocketRoute("/hello", hello_ws, name="hello_ws"),
])
```

### 路径参数

使用 `{name:type}` 可以标注路径参数，目前支持的类型有 `str`、`int`、`decimal`、`uuid` 和 `path`。

!!! tip
    如果路径参数的类型为 `str`，可以忽略掉 `:str`，直接使用 `{name}`。

!!! notice
    `path` 是极为特殊的参数类型，它只能出现在路径的最后，并且能匹配到所有的字符。

```python
from indexpy import Index
from indexpy.routing import HttpRoute, SocketRoute

app = Index()


@app.router.http("/{username:str}", method="get")
async def what_is_your_name(request):
    return request.path_params["username"]
```

### 注册多请求方法

注册处理 HTTP 请求的可调用对象为函数时，必须标注允许处理的 HTTP 方法，且只允许一种。需要为同一个路由注册处理不同 HTTP 方法的可调用对象，应使用类，并继承自 `HTTPView`。以下为示例代码，需要更详细的描述，应查看 [HTTP](../http/#_2) 章节。

```python
from indexpy import Index
from indexpy.http import HTTPView

app = Index()


@app.router.http("/cat")
class Cat(HTTPView):

    async def get(self):
        return self.request.method

    async def post(self):
        return self.request.method

    async def put(self):
        return self.request.method

    async def patch(self):
        return self.request.method

    async def delete(self):
        return self.request.method
```

### 反向查找

某些情况下，需要由路由名称反向生成对应的 URL 值，可以使用 `app.router.url_for`。

```python
from indexpy import Index

app = Index()


@app.router.http("/hello", name="hello", method="get")
@app.router.http("/hello/{name}", name="hello-name", method="get")
async def hello(request):
    return f"hello {request.path_params.get('name')}"


assert app.router.url_for("hello") == "/hello"
assert app.router.url_for("hello-name", {"name": "Aber"}) == "/hello/Aber"
```

!!! tip
    反向查找中，`websocket` 与 `http` 是互相独立的。通过 `protocol` 参数可以选择查找的路由，默认为 `http`。

## 路由列表

### Routes

当需要把某一些路由归为一组时，可使用 `Routes` 对象。`Routes` 对象也拥有 `.http`、`.websocket` 和 `.asgi` 方法，使用方法与 `app.router` 相同。

`Routes` 继承自 `typing.List`，所以它允许你使用类似于 Django 一样的路由申明方式，示例如下。

```python
from indexpy import Index
from indexpy.routing import Routes, HttpRoute

app = Index()


async def hello(request):
    return "hello world"


routes = Routes(
    HttpRoute("/hello", hello, method="get"),
)

app.router.extend(routes)
```

#### 名称空间

你可以为 `Routes` 设置 `namespace` 参数，这将在 `Routes` 对象中包含的每个路由名称（如果有的话）前加上 `namespace:`，以此来避免不同名称空间内的路由名称冲突。

#### 注册中间件

通过 `Routes` 你可以为整组路由注册一个或多个中间件。以下为简单的样例，仅用于表示如何注册中间件，关于中间件定义更详细的描述请查看[中间件章节](./middleware.md)。

```python
def one_http_middleware(endpoint):
    ...


def one_socket_middleware(endpoint):
    ...


def one_asgi_middleware(endpoint):
    ...


routes = Routes(
    ...,
    http_middlewares=[one_http_middleware],
    socket_middlewares=[one_socket_middleware],
    asgi_middlewares=[one_asgi_middleware]
)
```

当然，你同样可以使用装饰器来注册中间件，与上例的结果没有什么不同。

```python
routes = Routes(...)


@routes.http_middleware
def one_http_middleware(endpoint):
    ...


@routes.socket_middleware
def one_socket_middleware(endpoint):
    ...


@routes.asgi_middleware
def one_asgi_middleware(endpoint):
    ...
```

### SubRoutes

`SubRoutes` 是 `Routes` 的子类，它允许你更简单的定义子路由，而不是在每个路由上增加一个前缀。它同样拥有 `Routes` 一样的路由注册方式与中间件注册方式。

```python
subroutes = SubRoutes(
    "/hello",
    [
        HttpRoute("/world", ...),
        SocketRoute("/socket_world", ...),
    ],
),
```

### FileRoutes

!!! notice ""
    这也是 Index.py 此项目的命名来源之一。

`FileRoutes` 是一个特殊的路由列表，它允许你将某一个 `module` 下所有的 `.py` 文件一一对应到其相对路径相同的路由。

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

!!! tip
    你可以将文件名或文件夹名修改为 `module/{name}.py` 以此接受路径参数。

可以为 `FileRoutes` 设置 `suffix` 参数，给每个路由加上后缀，譬如 `suffix=".php"` 这将使路径看起来很像 PHP 😀。

### 路由组合

通过使用 `Routes` 对象与 `SubRoutes` 对象，你可以任意的构建路由，却不会有任何运行时的损耗——一切嵌套路由都会在代码加载时被展开。

```python
Routes(
    HttpRoute("/sayhi/{name}", ...),
    SubRoutes(
        "/hello",
        Routes(
            HttpRoute("/world", ...),
            SocketRoute("/socket_world", ...),
        ),
    ),
)
```

## 路由冲突

> 当多个路由匹配可以匹配到同一个 url path 时，称为路由冲突。

Index 做了大量的路由构造时检查，避免了很多没必要的路由错误与冲突，但仍然有一些路由冲突是一定会存在的。Index 的路由构造使用 Radix Tree，而遍历 Radix Tree 方式为深度优先遍历。但对于同一层级的节点来说，匹配顺序由插入顺序决定。

```python
app.router.extend([
    HttpRoute("/static/verify.txt", ...),
    HttpRoute("/static/{filepath:path}", ...),
])
```

- 在上例中，两个路由同为 `/static/` 节点下的子节点，故而在匹配 url 为 `/static/verify.txt` 的请求时，按照注册顺序，会匹配到第一条。
- 在下例中，`/static/verify/google.txt` 能匹配到的是第三条路由而不是第二条——因为第三条路由与第一条路由同为 `/static/verify/` 节点下的子节点，第二条路由属于 `/static/` 节点下，`/static/` 的子节点里优先匹配到 `verify` 节点与其子节点，后匹配 `{filepath:path}` 节点。故而匹配到第三条路由，而不是第二条。

```python
app.router.extend([
    HttpRoute("/static/verify/bing.txt", ...),
    HttpRoute("/static/{filepath:path}", ...),
    HttpRoute("/static/verify/google.txt", ...),
])
```

但如果注册顺序如下例，则 `/static/verify/google.txt` 匹配到的路由为第一条，

```python
app.router.extend([
    HttpRoute("/static/{filepath:path}", ...),
    HttpRoute("/static/verify/bing.txt", ...),
    HttpRoute("/static/verify/google.txt", ...),
])
```
