# Web Server Gateway Interface

WSGI(Web Server Gateway Interface) 诞生自 2003 年，其生态在 2023 年远比 ASGI 生态成熟。如果你的程序不需要使用 `async`/`await`，那么使用 WSGI 模式的 Kuí 会更加合适。

WSGI 模式下的 Kuí 使用方式与 ASGI 模式下的 Kuí 使用方式几乎相同。只有三点区别：

- WSGI 模式是完全同步的，不支持 `async`/`await`。
- WSGI 模式没有 Lifespan（`on_startup` 和 `on_shutdown`）。
- WSGI 模式暂不支持 WebSocket（很多时候你可以使用 Server-sent Events 代替 WebSocket）。
