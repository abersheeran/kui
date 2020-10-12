## Index

`Index` 对象作为 Index.py 程序的入口，推荐每个项目里始终只使用一个 `Index` 对象。

!!! tip
    通过 `scope["app"]`、`request["app"]` 或 `websocket["app"]` 可以获取到正在使用的 `Index` 对象。

### `__init__`

它有许多初始化参数，可用于控制一些 Application 内的程序逻辑。

- **`templates: typing.Iterable[str] = ()`**：此参数用于控制 Index 去哪些地方寻找模板。

    1. 模板在项目内：使用相对路径即可。
    2. 需要使用其他包里的模板（例如 `site-packages` 里的包）：使用 `package:path` 的格式。

- **`try_html: bool = True`**：寻找不到路由时，自动尝试使用同名模板。默认开启。

- **`on_startup: typing.List[typing.Callable]`**：服务启动后自动调用的函数列表；默认为空。

- **`on_shutdown: typing.List[typing.Callable]`**：服务关闭前自动调用的函数列表；默认为空。

- **`factory_class: FactoryClass`**：通过覆盖此参数，可以自定义整个 Index 作用域中使用的 `Request` 类与 `WebSocket` 类。

### `jinja_env`

此属性是一个 `jinja2.Environment` 对象，`TemplateResponse` 将使用它对模板进行寻找、渲染。

通过读写它的 [`globals`](https://jinja.palletsprojects.com/en/2.11.x/api/#jinja2.Environment.globals) 对象，可以把函数或者变量注入全局。

!!! notice
    Index 内置的 `jinja_env` 默认开启了 `enable_async` 选项，这意味着你可以传入 `async def` 定义的异步函数。但在模板中，可以像调用普通函数一样调用它——异步等待是自动的。

### `factory_class`

通过读取此属性，你可以获取到当前 Index 实例下，所有 `Request`、`WebSocket` 的类定义。需要实例化这些对象时，推荐从 `scope["app"]factory_class` 中读取它们的类定义。

### `router`

所有的路由最终都将归入此路由对象中，此对象有四个方法：

- `append`：追加一个新路由到路由树中。
- `extend`：追加一个列表的新路由到路由树中。
- `search`：为请求寻找一个合适的 `endpoint` 并返回路径参数。
- `url_for`：通过路由名称与路径参数反向构建完整的 URL path。

## Dispatcher

`Dispatcher` 可以用于组合多个 ASGI 应用。以下为一个简单的用例，当一个新的请求 `/django/admin/` 到达 `app` 时，按照顺序依次调用 `django_app`、`other_django_app`，第一个非 404 的响应将会作为最后的结果返回给客户端。如果所有的 Application 都返回 404 响应且未读取请求体，则最终由 `application` 来处理此次请求；如果有任意一个 Application 读取了请求体且返回 404 响应，则会调用 `handle404` 返回响应（默认是一个空内容的 404 响应，你可以在参数里覆盖它）。

```python
from a2wsgi import WSGIMiddleware
from indexpy import Index, Dispatcher

from django_app_name.wsgi import application as django_app
from other_django_app_name.wsgi import application as other_django_app
from fastapi_app import app as fastapi_app

application = Index()

app = Dispatcher(
    application,
    ("/django", WSGIMiddleware(django_app)),
    ("/django", WSGIMiddleware(other_django_app)),
    ("/some", fastapi_app),
)
```

!!! notice
    使用 `pip install a2wsgi` 安装 `a2wsgi`，可以使用 `a2wsgi.WSGIMiddleware` 将一个 `WSGI` 应用转换为 `ASGI` 应用。
