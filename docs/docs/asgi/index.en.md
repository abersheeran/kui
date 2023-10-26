# Asynchronous Server Gateway Interface

ASGI (Asynchronous Server Gateway Interface) was introduced in 2018. If your program requires the use of `async`/`await`, then using Kuí in ASGI mode would be more suitable.

In ASGI mode, the usage of Kuí is very similar to that in WSGI mode, with only three differences:

- ASGI mode is asynchronous and supports `async`/`await`.
- ASGI mode includes Lifespan (`on_startup` and `on_shutdown`).
- ASGI mode supports WebSocket.
