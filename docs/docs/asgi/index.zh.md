# Asynchronous Server Gateway Interface

ASGI(Asynchronous Server Gateway Interface) 诞生自 2018 年。如果你的程序需要使用 `async`/`await`，那么使用 ASGI 模式的 Kuí 会更加合适。

ASGI 模式下的 Kuí 使用方式与 WSGI 模式下的 Kuí 使用方式几乎相同。只有三点区别：

 - ASGI 模式是异步的，支持 `async`/`await`。
 - ASGI 模式有 Lifespan（`on_startup` 和 `on_shutdown`）。
 - ASGI 模式支持 WebSocket。
