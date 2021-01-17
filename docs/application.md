## Index

`Index` 对象作为 Index.py 程序的入口，推荐每个项目里始终只使用一个 `Index` 对象。

!!! tip
    通过 `scope["app"]`、`request.app` 或 `websocket.app` 可以获取到正在使用的 `Index` 对象。

它有许多初始化参数，可用于控制一些 Application 内的程序逻辑。

- **`debug: bool = False`**, 用于设置是否使用调试模式下的 `Index`。

- **`templates: Optional[BaseTemplates] = None`**：此参数用于控制 `indexpy.http.responses.TemplateResponse` 的具体行为。

- **`on_startup: List[Callable] = []`**：服务启动后自动调用的函数列表。

- **`on_shutdown: List[Callable] = []`**：服务关闭前自动调用的函数列表。

- **`routes: List[BaseRoute] = []`**：路由列表。

- **`middlewares: List[Middleware] = []`**：挂载于 Index-py 对象上 ASGI 中间件列表。

- **`exception_handlers = {}`**：处理异常的函数字典。键为 `int` 或 `Exception` 实例，值为对应的函数（定义可参考[自定义异常处理](./http.md#_8)）。

- **`factory_class: FactoryClass`**：通过覆盖此参数，可以自定义整个 Index-py 作用域中使用的 `Request` 类与 `WebSocket` 类。
