Kuí's routing is based on [Radix Tree](https://en.wikipedia.org/wiki/Radix_tree).

## Basic Usage

### Using Decorators

Similar to frameworks like bottle/flask, Kuí supports registering routes using decorators. In the example below, `name` is the route name, which is used for reverse route lookup.

```python
from kui.wsgi import Kui

app = Kui()


@app.router.http("/hello", name="hello")
def hello():
    ...
```

!!! tip
    If `name` is not specified, the `__name__` attribute of the registered callable object will be used as the default name.

!!! notice
    If the specified route `name` is `None`, the route cannot be found using `name`.

### Route Objects

In fact, the decorator route declaration is a shortcut for the following method:

```python
from kui.wsgi import Kui, HttpRoute

app = Kui()


def hello():
    ...


app.router << HttpRoute("/hello", hello, name="hello")
```

The route object in Kuí is as follows.

```python
# Http
HttpRoute(path: str, endpoint: Any, name: Optional[str] = "")
```

- `path` specifies the string that the route can match

- `endpoint` specifies the callable object corresponding to the route

- `name` specifies the name of the route. When `name` is `None`, the route will have no name; when `name` is `""`, the `endpoint.__name__` will be automatically used as the route name.

#### Middleware

You can use decorators on route objects, which will be applied to the endpoint but differ from directly using decorators on the endpoint itself. The decorators are applied to the endpoint after Kuí's preprocessing.

!!! notice
    In this document, decorators registered in this way are referred to as middleware. The term "middleware" is mainly used to maintain consistency with other frameworks.

```python
HttpRoute(...) @ decorator
```

Just like registering regular decorators, you can register multiple decorators, and they will be executed in order from outermost to innermost.

```python
HttpRoute(...) @ decorator1 @ decorator2 @ decorator3
```

You can also register middleware when using decorators for route registration, as shown below, and the execution order is from right to left.

```python
@app.router.http("/path", middlewares=[decorator1, decorator2, decorator3])
def path(): ...
```

### Limiting Request Methods

!!! notice
    When specifying support for the GET method, HEAD will be automatically allowed.

!!! tip
    When limiting the request method, OPTIONS requests will be automatically handled. Otherwise, you need to handle the OPTIONS method yourself.

When registering with decorators, you can directly limit the request methods that the route can accept. Currently, only the following five HTTP methods are supported for limiting. If you don't specify any, all request methods are allowed by default.

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

The above code internally uses the `required_method` decorator to achieve the purpose of limiting request methods. You can also manually register the decorator, which allows you to limit more types of requests. Here is an example:

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

### List-Style Registration

Kuí also supports list-style registration similar to Django:

```python
from kui.wsgi import Kui, HttpRoute


def hello():
    return "hello world"


app = Kui(routes=[
    HttpRoute("/hello", hello, name="hello"),
])
```

### Path Parameters

You can use `{name:type}` to mark path parameters, and the currently supported types are `str`, `int`, `decimal`, `date`, `uuid`, and `any`.

!!! tip
    If the type of the path parameter is `str`, you can omit `:str` and directly use `{name}`.

!!! notice
    `str` cannot match `/`, if you need to match `/`, use `any`.

!!! notice
    `any` is a very special parameter type. It can only appear at the end of the path and can match any character.

```python
from kui.wsgi import Kui, request

app = Kui()


@app.router.http("/{username:str}")
def what_is_your_name():
    return request.path_params["username"]
```

### Reverse Lookup

In some cases, you may need to generate the corresponding URL value based on the route name. You can use `app.router.url_for` for this purpose.

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

## Route Groups

When you need to group certain routes together, you can use the `Routes` object.

The `Routes` object has an `.http` method that allows you to register routes using decorators, similar to `app.router`.

`Routes` also allows you to use route declarations similar to Django, as shown in the example below.

```python
from kui.wsgi import Routes, HttpRoute


def hello(request):
    return "hello world"


routes = Routes(
    HttpRoute("/hello", hello),
)
```

You can register all routes in a `Routes` object to `app.router` using the `<<` operator, and the result of this operation is `app.router`, which means you can chain the calls.

```python
from .app1.urls import routes as app1_routes
from .app2.urls import routes as app2_routes

app.router << app1_routes << app2_routes
```

Of course, you can also pass it directly when initializing the `Kui` object.

```python
from kui.wsgi import Kui

from .app1.urls import routes as app1_routes

app = Kui(routes=app1_routes)
```

### Route Combination

`Routes` can be easily combined with other `Routes` objects.

```python
from .app1.urls import routes as app1_routes

routes = Routes(...) << app1_routes
```

And the result of `<<` is the left-hand `Routes` object, which means you can chain it, as shown below.

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

### Namespaces

You can set the `namespace` parameter for `Routes`, which will prefix every route name (if any) in the `Routes` object with `namespace:`, avoiding conflicts between route names in different namespaces.

```python
routes = Routes(..., namespace="namespace")
```

!!! notice ""

    When using `app.router.url_for`, don't forget to add the namespace prefix of the route.

### Middleware Registration

With `Routes`, you can register one or more middleware for the entire group of routes. Here is a simple example:

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

### Common Prefix

Sometimes you may want to place a group of routes under the same prefix. The following two code snippets produce the same result:

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

This operation creates a completely new sequence of routes and does not affect the original route sequence. Therefore, you can repeat the `//` operation on the same `Routes` object.

```python
routes = ("/admin" // auth_routes) + ("/account" // auth_routes)
```

!!! Warning "Note"

    When using `routes = "prefix" // Routes(......)` and then calling `@routes.http` to register routes, the subsequent routes will not automatically be prefixed with `"prefix"`. You should perform the `"prefix" // routes` operation after all routes within a route group have been registered.

## Other Route Groups

By constructing a sequence of route objects, you can write your preferred route registration style, and they will all be merged into the Radix Tree.

### MultimethodRoutes

`MultimethodRoutes` is a special sequence of routes that allows you to register routes in the following way, splitting different methods under the same PATH into multiple functions without explicitly using classes. Other than that, it is the same as `Routes`.

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
