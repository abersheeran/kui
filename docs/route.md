Index 的路由与 Python 传统的 web 框架不同，传统框架的路由寻找方式大多为穷举遍历，虽然实现简单，但效率较低。而 Index 基于 [Radix Tree](https://en.wikipedia.org/wiki/Radix_tree)，即灵活又高效。

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
```

!!! tip
    如果 `name` 没有被指定，则会默认使用被注册的可调用对象的 `__name__` 属性。

!!! notice
    如果指定路由的 `name` 为 `None`，则无法通过 `name` 查找到该路由。

### 申明式注册

除了装饰器用法，你也可以采取申明式，这两种方法是等价的。

```python
from indexpy import Index

app = Index()


async def hello(request):
    return "hello world"


async def hello_ws(websocket):
    ...


app.router.http("/hello", hello, name="hello", method="get")
app.router.websocket("/hello", hello_ws, name="hello_ws")
```

### 路由对象

事实上，如上两种路由申明方式都是如下方法的快捷方式

```python
from indexpy import Index
from indexpy.routing import HttpRoute, SocketRoute

app = Index()


async def hello(request):
    return "hello world"


async def hello_ws(websocket):
    ...


app.router.append(HttpRoute("/hello", hello, name="hello", method="get"))
app.router.append(SocketRoute("/hello", hello_ws, name="hello_ws"))
```

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

使用 `{name:type}` 可以标注路径参数，在视图中使用 `path` 参数(`dict` 类型)接受全部的路径参数。目前支持的类型有 `str`、`int`、`decimal`、`uuid` 和 `path`。

!!! tip
    如果路径参数的类型为 `str`，可以忽略掉 `:str`，直接使用 `{name}`。

!!! notice
    `path` 是极为特殊的参数类型，它只能出现在路径的最后，并且能匹配到所有的字符。

```python
from indexpy import Index
from indexpy.routing import HttpRoute, SocketRoute

app = Index()


@app.router.http("/{username:str}", method="get")
async def what_is_your_name(request, path):
    return path["username"]
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
async def hello(request, path):
    return f"hello {path['name']}"


assert app.router.url_for("hello") == "/hello"
assert app.router.url_for("hello-name", {"name": "Aber"}) == "/hello/Aber"
```

!!! tip
    反向查找中，`websocket` 与 `http` 是互相独立的。通过 `protocol` 参数可以选择查找的路由，默认为 `http`。

## Routes

当需要把某一些路由归为一组时，可使用 `Routes` 对象。`Routes` 对象也拥有 `.http` 与 `.websocket` 方法，使用方法与 `app.router` 相同。

`Routes` 允许你使用类似于 Django 一样的路由申明方式，示例如下。

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

!!! notice
    **不要忘记**使用 `app.router.extend(routes)` 将 `Routes` 对象注册进 `app.router` 中。

### 注册中间件

通过 `Routes` 你可以为整组路由注册一个或多个中间件。以下为简单的样例，关于中间件定义更详细的描述请查看[中间件章节](../middleware/)。

```python
def http_only_print(endpoint):
    async def wrapper(request):
        print("http middleware start")
        response = convert(await endpoint(request))
        print("http middleware end")
        return response

    return wrapper


def socket_only_print(endpoint):
    async def wrapper(websocket):
        print("socket middleware start")
        await endpoint(websocket)
        print("socket middleware end")

    return wrapper


routes = Routes(
    ...,
    http_middlewares=[http_only_print],
    socket_middlewares=[socket_only_print],
)
```

当然，你同样可以使用装饰器来注册中间件，与上例的结果没有什么不同。

```python
routes = Routes(...)


@routes.http_middleware
def http_only_print(endpoint):
    async def wrapper(request):
        print("http middleware start")
        response = convert(await endpoint(request))
        print("http middleware end")
        return response

    return wrapper


@routes.socket_middleware
def socket_only_print(endpoint):
    async def wrapper(websocket):
        print("socket middleware start")
        await endpoint(websocket)
        print("socket middleware end")

    return wrapper
```

### 子路由

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
