Kuí 的路由基于 [Radix Tree](https://en.wikipedia.org/wiki/Radix_tree)。

## 基本用法

### 使用装饰器

与 bottle/flask 之类的框架一样，Kuí 支持使用装饰器注册路由。下面的例子里，`name` 是路由名称，这在反向查找路由时会起到作用。

```python
from kui.wsgi import Kui

app = Kui()


@app.router.http("/hello", name="hello")
def hello():
    ...
```

!!! tip
    如果 `name` 没有被指定，则会默认使用被注册的可调用对象的 `__name__` 属性。

!!! notice
    如果指定路由的 `name` 为 `None`，则无法通过 `name` 查找到该路由。

### 路由对象

事实上，装饰器路由申明方式是如下方法的快捷方式

```python
from kui.wsgi import Kui, HttpRoute

app = Kui()


def hello():
    ...


app.router << HttpRoute("/hello", hello, name="hello")
```

Kuí 的路由对象如下。

```python
# Http
HttpRoute(path: str, endpoint: Any, name: Optional[str] = "")
```

- `path` 指定路由能匹配到的字符串

- `endpoint` 指定路由对应的可调用对象

- `name` 为路由指定名称，`name` 为 `None` 时，此路由将没有名称；`name` 为 `""` 时，将自动读取 `endpoint.__name__` 作为路由名称。

#### 中间件

你可以对路由对象使用装饰器，这将会作用到 endpoint 上，但与直接对 endpoint 使用装饰器不同的是它作用于 Kuí 预处理后的 endpoint 上。

!!! notice
    在本文档里，这样注册的装饰器被称为中间件。“中间件”这一名称主要是为了沿用其他框架中的说法。

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
def path(): ...
```

### 限定请求方法

!!! notice
    指定支持 GET 方法时，HEAD 将被自动允许。

!!! tip
    限定了请求方法后，OPTIONS 的请求将被自动处理。反之，你需要自行处理 OPTIONS 方法。

在使用装饰器注册时可以直接限定该路由能够接受的请求方法，目前仅支持以下五种 HTTP 方法的限定。如果你没有指定，则默认允许所有请求方法。

```python
from kui.wsgi import Kui

app = Kui()


@app.router.http.get("/get")
def need_get():
    ...


@app.router.http.post("/post")
def need_post():
    ...


@app.router.http.put("/put")
def need_put():
    ...


@app.router.http.patch("/patch")
def need_patch():
    ...


@app.router.http.delete("/delete")
def need_delete():
    ...
```

如上代码是在内部使用了 `required_method` 装饰器来达到限定请求方法的目的，你也可以选择手动注册装饰器，这将能限定更多种类的请求。代码样例如下：

```python
from kui.wsgi import Kui, required_method

app = Kui()


@app.router.http("/get", middlewares=[required_method("GET")])
def need_get():
    ...


@app.router.http("/connect", middlewares=[required_method("CONNECT")])
def need_connect():
    ...
```

### 列表式注册

Kuí 同样支持类似于 Django 的列表式写法：

```python
from kui.wsgi import Kui, HttpRoute


def hello():
    return "hello world"


app = Kui(routes=[
    HttpRoute("/hello", hello, name="hello"),
])
```

### 路径参数

使用 `{name:type}` 可以标注路径参数，目前支持的类型有 `str`、`int`、`decimal`、`date`、`uuid` 和 `any`。

!!! tip
    如果路径参数的类型为 `str`，可以忽略掉 `:str`，直接使用 `{name}`。

!!! notice
    `str` 不能匹配到 `/`，如果需要匹配 `/` 请使用 `any`。

!!! notice
    `any` 是极为特殊的参数类型，它只能出现在路径的最后，并且能匹配到所有的字符。

```python
from kui.wsgi import Kui, request

app = Kui()


@app.router.http("/{username:str}")
def what_is_your_name():
    return request.path_params["username"]
```

### 反向查找

某些情况下，需要由路由名称反向生成对应的 URL 值，可以使用 `app.router.url_for`。

```python
from kui.wsgi import Kui, request

app = Kui()


@app.router.http("/hello", name="hello")
@app.router.http("/hello/{name}", name="hello-with-name")
def hello():
    return f"hello {request.path_params.get('name')}"


assert app.router.url_for("hello") == "/hello"
assert app.router.url_for("hello-with-name", {"name": "Aber"}) == "/hello/Aber"
```

## 路由分组

当需要把某一些路由归为一组时，可使用 `Routes` 对象。

`Routes` 对象拥有 `.http` 方法允许你使用装饰器方式注册路由，使用方法与 `app.router` 相同。

`Routes` 也同样允许你使用类似于 Django 一样的路由申明方式，示例如下。

```python
from kui.wsgi import Routes, HttpRoute


def hello(request):
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

当然，你也可以直接在初始化 `Kui` 对象时传入。

```python
from kui.wsgi import Kui

from .app1.urls import routes as app1_routes

app = Kui(routes=app1_routes)
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
    def wrapper():
        return endpoint()
    return wrapper


routes = Routes(
    ...,
    http_middlewares=[one_http_middleware],
)
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

这种运算会创建全新的路由序列，对原本的路由序列不会造成影响，故而你可以重复对同一个 `Routes` 对象调用 `//` 方法。

```python
routes = ("/admin" // auth_routes) + ("/account" // auth_routes)
```

!!! Warning "注意事项"

    在使用 `routes = "prefix" // Routes(......)` 之后再调用 `@routes.http` 等方法注册路由时，并不会给后续的路由自动加上 `"prefix"` 前缀。你应当在一个路由分组内所有路由注册完成之后，再进行 `"prefix" // routes` 运算。

## 其他路由分组

通过构建路由对象的序列可以编写自己喜爱的路由注册方式，在最终都会合并进 Radix Tree 里。

### MultimethodRoutes

`MultimethodRoutes` 是一个特殊的路由序列，它允许你使用如下方式注册路由，在不显式使用类的情况下拆分同一个 PATH 下的不同方法到多个函数中。除此之外，均与 `Routes` 相同。

```python
from kui.wsgi import Kui, MultimethodRoutes, HttpView

routes = MultimethodRoutes(base_class=HttpView)


@routes.http.get("/user")
def list_user():
    pass


@routes.http.post("/user")
def create_user():
    pass


@routes.http.delete("/user")
def delete_user():
    pass
```
