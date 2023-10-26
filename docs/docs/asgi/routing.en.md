Kuí's routing is based on [Radix Tree](https://en.wikipedia.org/wiki/Radix_tree).

## Basic Usage

### Using Decorators

Similar to frameworks like Bottle/Flask, Kuí supports registering routes using decorators. In the example below, `name` is the route name, which is used for reverse route lookup.

```python
from kui.asgi import Kui

app = Kui()


@app.router.http("/hello", name="hello")
async def hello():
    ...


@app.router.socket("/ws", name="echo")
async def echo():
    ...
```

!!! tip
    If `name` is not specified, the registered callable object's `__name__` attribute will be used as the route name by default.

!!! notice
    If the `name` of a route is set to `None`, the route cannot be found using `name`.

### Route Objects

In fact, the decorator route declaration is a shortcut for the following methods:

```python
from kui.asgi import Kui, HttpRoute, SocketRoute

app = Kui()


async def hello():
    ...


async def echo():
    ...


app.router << HttpRoute("/hello", hello, name="hello")
app.router << SocketRoute("/ws", echo, name="echo")
```

The route objects in Kuí are as follows:

```python
# Http
HttpRoute(path: str, endpoint: Any, name: Optional[str] = "")
# WebSocket
SocketRoute(path: str, endpoint: Any, name: Optional[str] = "")
```

- `path` specifies the string that the route can match

- `endpoint` specifies the callable object corresponding to the route

- `name` specifies the name of the route. When `name` is `None`, the route will have no name; when `name` is `""`, the `endpoint.__name__` will be automatically used as the route name.

#### Middleware

You can use decorators on route objects, which will be applied to the endpoint. However, unlike using decorators directly on the endpoint, it applies to the Kuí preprocessed endpoint.

!!! notice
    In this document, the decorators registered in this way are called middleware. The term "middleware" is mainly used to be consistent with other frameworks.

```python
HttpRoute(...) @ decorator
```

You can register multiple decorators in the same way as registering regular decorators, and they will be executed from outer to inner.

```python
HttpRoute(...) @ decorator1 @ decorator2 @ decorator3
```

Furthermore, you can register middleware when using decorators for route registration, as shown below. The execution order is also from right to left.

```python
@app.router.http("/path", middlewares=[decorator1, decorator2, decorator3])
async def path(): ...
```

### Restricting Request Methods

!!! notice
    When specifying support for the GET method, HEAD will be automatically allowed.

!!! tip
    When request methods are restricted, OPTIONS requests will be handled automatically. Otherwise, you need to handle OPTIONS requests manually.

When registering routes using decorators, you can directly restrict the request methods that the route can accept. Currently, only the following five HTTP methods are supported for restriction. If you don't specify any methods, all request methods are allowed by default.

```python
from kui.asgi import Kui

app = Kui()


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

The above code internally uses the `required_method` decorator to achieve method restriction. You can also manually register the decorator, which allows for more types of requests. The code example is as follows:

```python
from kui.asgi import Kui, required_method

app = Kui()


@app.router.http("/get", middlewares=[required_method("GET")])
async def need_get():
    ...


@app.router.http("/connect", middlewares=[required_method("CONNECT")])
async def need_connect():
    ...
```

### List-Based Registration

Kuí also supports list-based registration similar to Django:

```python
from kui.asgi import Kui, HttpRoute


async def hello():
    return "hello world"


app = Kui(routes=[
    HttpRoute("/hello", hello, name="hello"),
])
```

### Path Parameters

You can use `{name:type}` to specify path parameters. Currently supported types are `str`, `int`, `decimal`, `date`, `uuid`, and `any`.

!!! tip
    If the type of a path parameter is `str`, you can omit `:str` and directly use `{name}`.

!!! notice
    `str` cannot match `/`. If you need to match `/`, use `any`.

!!! notice
    `any` is a very special parameter type. It can only appear at the end of the path and can match any character.

```python
from kui.asgi import Kui, request

app = Kui()


@app.router.http("/{username:str}")
async def what_is_your_name():
    return request.path_params["username"]
```

### Reverse Lookup

In some cases, you may need to generate the corresponding URL value based on the route name. You can use `app.router.url_for` for this purpose.

```python
from kui.asgi import Kui, request

app = Kui()


@app.router.http("/hello", name="hello")
@app.router.http("/hello/{name}", name="hello-with-name")
async def hello():
    return f"hello {request.path_params.get('name')}"


assert app.router.url_for("hello") == "/hello"
assert app.router.url_for("hello-with-name", {"name": "Aber"}) == "/hello/Aber"
```

## Route Grouping

When you need to group certain routes together, you can use the `Routes` object.

The `Routes` object has an `.http` method that allows you to register routes using decorators, similar to `app.router`.

`Routes` also allows you to use route declaration similar to Django, as shown in the example below.

```python
from kui.asgi import Routes, HttpRoute


async def hello(request):
    return "hello world"


routes = Routes(
    HttpRoute("/hello", hello),
)
```

You can register all routes in a `Routes` object to `app.router` using the `<<` operator, and the result of this operation is `app.router`. This means you can chain the calls.

```python
from .app1.urls import routes as app1_routes
from .app2.urls import routes as app2_routes

app.router << app1_routes << app2_routes
```

Alternatively, you can pass it directly when initializing the `Kui` object.

```python
from kui.asgi import Kui

from .app1.urls import routes as app1_routes

app = Kui(routes=app1_routes)
```

### Route Combination

`Routes` can be easily combined with other `Routes` objects.

```python
from .app1.urls import routes as app1_routes

routes = Routes(...) << app1_routes
```

The result of `<<` is the left-hand `Routes` object, which means you can chain it, as shown below.

```python
from .app1.urls import routes as app1_routes
from .app2.urls import routes as app2_routes


Routes() << app1_routes << app2_routes
```

You can also merge two `Routes` objects into a new `Routes` object instead of merging one into the other.

```python
from .app1.urls import routes as app1_routes
from .app2.urls import routes as app2_routes


new_routes = app1_routes + app2_routes
```

### Namespace

You can set a `namespace` parameter for `Routes`, which will add the `namespace:` prefix to the name of each route (if any) in the `Routes` object. This helps avoid route name conflicts between different namespaces.

```python
routes = Routes(..., namespace="namespace")
```

!!! notice ""

    When using `app.router.url_for`, don't forget to add the namespace prefix of the route.

### Middleware Registration

With `Routes`, you can register one or more middleware for the entire group of routes. Here is a simple example:

```python
async def one_http_middleware(endpoint):
    async def wrapper():
        return await endpoint()
    return wrapper


async def one_socket_middleware(endpoint):
    async def wrapper():
        await endpoint()
    return wrapper


routes = Routes(
    ...,
    http_middlewares=[one_http_middleware],
    socket_middlewares=[one_socket_middleware]
)
```

### Common Prefix

Sometimes you may want to group routes under the same prefix. The following two code snippets have the same result.

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

This operation creates a completely new route sequence and does not affect the original route sequence. Therefore, you can repeat the `//` operation on the same `Routes` object.

```python
routes = ("/admin" // auth_routes) + ("/account" // auth_routes)
```

!!! Warning "Note"

    When using `routes = "prefix" // Routes(......)`, the subsequent routes registered using `@routes.http` will not automatically have the `"prefix"` prefix. You should perform the `"prefix" // routes` operation after all routes in a route group have been registered.

## Other Route Grouping

By building a sequence of route objects, you can write your preferred route registration style, and they will all be merged into the Radix Tree.

### MultimethodRoutes

`MultimethodRoutes` is a special route sequence that allows you to register routes using the following method, splitting different methods under the same PATH to multiple functions without explicitly using classes. Other than that, it is the same as `Routes`.

```python
from kui.asgi import Kui, MultimethodRoutes, HttpView

routes = MultimethodRoutes(base_class=HttpView)


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
