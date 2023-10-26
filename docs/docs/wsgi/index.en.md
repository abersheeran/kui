# Web Server Gateway Interface

The Web Server Gateway Interface (WSGI) was born in 2003, and its ecosystem is much more mature in 2023 compared to the ASGI ecosystem. If your program doesn't need to use `async`/`await`, then using Kuí in WSGI mode would be more suitable.

In WSGI mode, the usage of Kuí is almost the same as in ASGI mode, with only three differences:

- WSGI mode is completely synchronous and does not support `async`/`await`.
- WSGI mode does not have Lifespan (`on_startup` and `on_shutdown`).
- WSGI mode does not currently support WebSocket (in many cases, you can use Server-sent Events as an alternative to WebSocket).
