# WebSocket

!!! note
    WebSocket is only available in ASGI mode. For WSGI, consider using [Server-Sent Events](http.md#sendeventresponse-server-sent-events) as an alternative.

## Function Handlers

Handle WebSocket connections with a function:

```python
from kui.asgi import websocket

@app.router.websocket("/ws")
async def ws_handler():
    await websocket.accept()
    async for data in websocket.iter_json():
        await websocket.send_json({"echo": data})
```

Function handlers must manage the connection lifecycle manually (accept, receive/send, close).

!!! warning
    Avoid polling with `websocket.is_disconnected()` — it may discard client messages. Prefer `websocket.iter_json()` or catch `WebSocketDisconnect` from receive calls instead.

## Class-Based Views (SocketView)

For structured WebSocket handling:

```python
from kui.asgi import SocketView, websocket

@app.router.websocket("/chat")
class ChatView(SocketView):
    encoding = "json"  # "text" | "bytes" | "json" | "anystr"

    async def on_connect(self):
        await websocket.accept()

    async def on_receive(self, data):
        await websocket.send_json({"echo": data})

    async def on_disconnect(self, close_code: int):
        pass
```

### Lifecycle Methods

| Method | Description |
|---|---|
| `on_connect()` | Called when client initiates connection. Call `await websocket.accept()` here. |
| `on_receive(data)` | Called for each message. `data` type depends on `encoding`. |
| `on_disconnect(close_code)` | Called when connection closes. |

### Encoding Options

| Encoding | `data` type in `on_receive` | Description |
|---|---|---|
| `"anystr"` | `str` or `bytes` | Accept text or binary messages |
| `"text"` | `str` | Text messages only |
| `"bytes"` | `bytes` | Binary messages only |
| `"json"` | `Any` | JSON-decoded messages |

## WebSocket Object

Access the current WebSocket via the `websocket` context variable:

```python
from kui.asgi import websocket
```

### Connection Management

```python
await websocket.accept()
await websocket.close(code=1000)
is_closed = await websocket.is_disconnected()
```

### Sending Data

```python
await websocket.send_text("hello")
await websocket.send_bytes(b"\x00\x01")
await websocket.send_json({"key": "value"})
```

### Receiving Data

```python
text = await websocket.receive_text()
data = await websocket.receive_bytes()
obj = await websocket.receive_json()

# Iterate JSON messages until disconnect
async for msg in websocket.iter_json():
    print(msg)
```

### Connection Attributes

| Attribute | Type | Description |
|---|---|---|
| `websocket.url` | `URL` | Connection URL |
| `websocket.headers` | `Headers` | HTTP headers from handshake |
| `websocket.query_params` | `QueryParams` | Query string parameters |
| `websocket.path_params` | `dict` | Extracted path parameters |
| `websocket.client` | `Address` | Client address |
| `websocket.cookies` | `dict` | Cookies |
| `websocket.state` | `State` | Per-connection mutable state |
| `websocket.app` | `Kui` | Application instance |

## WebSocket with Parameters

WebSocket handlers support parameter binding:

```python
from typing_extensions import Annotated
from kui.asgi import Query

@app.router.websocket("/ws")
class AuthenticatedWS(SocketView):
    encoding = "json"

    async def on_connect(self):
        await websocket.accept()

    async def on_receive(self, data):
        await websocket.send_json(data)
```

Query parameters can be extracted via `Annotated` in function-style handlers or via `websocket.query_params` directly.

## WebSocket Routing

Register WebSocket routes with decorators or route objects:

```python
# Decorator
@app.router.websocket("/ws", name="websocket")
async def ws_handler():
    ...

# Route object
from kui.asgi import SocketRoute

app.router <<= SocketRoute("/ws", ws_handler, name="websocket")
```

WebSocket routes can also be grouped with `Routes`:

```python
from kui.asgi import Routes, SocketRoute

ws_routes = Routes(
    SocketRoute("/chat", chat_handler),
    SocketRoute("/notifications", notify_handler),
)
app.router <<= "/ws" // ws_routes
```

## WebSocket Middleware

Apply middleware to WebSocket routes:

```python
app.router <<= SocketRoute("/ws", handler) @ ws_auth_middleware

# App-level WebSocket middleware
app = Kui(socket_middlewares=[ws_logging_middleware])
```
