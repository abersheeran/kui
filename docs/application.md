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
