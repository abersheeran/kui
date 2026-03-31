# WebSocket

!!! note
    WebSocket 仅在 ASGI 模式下可用。WSGI 模式下可考虑使用 [Server-Sent Events](http.md#sendeventresponseserver-sent-events) 作为替代方案。

## 函数处理器

使用函数处理 WebSocket 连接：

```python
from kui.asgi import websocket

@app.router.websocket("/ws")
async def ws_handler():
    await websocket.accept()
    async for data in websocket.iter_json():
        await websocket.send_json({"echo": data})
```

函数处理器必须手动管理连接生命周期（接受、收发、关闭）。

!!! warning
    避免使用 `websocket.is_disconnected()` 轮询——它可能会丢弃客户端消息。建议使用 `websocket.iter_json()` 或在接收调用中捕获 `WebSocketDisconnect`。

## 基于类的视图（SocketView）

用于结构化的 WebSocket 处理：

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

### 生命周期方法

| 方法 | 说明 |
|---|---|
| `on_connect()` | 客户端发起连接时调用。在此调用 `await websocket.accept()`。 |
| `on_receive(data)` | 收到每条消息时调用。`data` 类型取决于 `encoding`。 |
| `on_disconnect(close_code)` | 连接关闭时调用。 |

### 编码选项

| 编码 | `on_receive` 中的 `data` 类型 | 说明 |
|---|---|---|
| `"anystr"` | `str` 或 `bytes` | 接受文本或二进制消息 |
| `"text"` | `str` | 仅文本消息 |
| `"bytes"` | `bytes` | 仅二进制消息 |
| `"json"` | `Any` | JSON 解码后的消息 |

## WebSocket 对象

通过 `websocket` 上下文变量访问当前 WebSocket：

```python
from kui.asgi import websocket
```

### 连接管理

```python
await websocket.accept()
await websocket.close(code=1000)
is_closed = await websocket.is_disconnected()
```

### 发送数据

```python
await websocket.send_text("hello")
await websocket.send_bytes(b"\x00\x01")
await websocket.send_json({"key": "value"})
```

### 接收数据

```python
text = await websocket.receive_text()
data = await websocket.receive_bytes()
obj = await websocket.receive_json()

# 迭代 JSON 消息直到断开
async for msg in websocket.iter_json():
    print(msg)
```

### 连接属性

| 属性 | 类型 | 说明 |
|---|---|---|
| `websocket.url` | `URL` | 连接 URL |
| `websocket.headers` | `Headers` | 握手时的 HTTP 头部 |
| `websocket.query_params` | `QueryParams` | 查询字符串参数 |
| `websocket.path_params` | `dict` | 提取的路径参数 |
| `websocket.client` | `Address` | 客户端地址 |
| `websocket.cookies` | `dict` | Cookie |
| `websocket.state` | `State` | 每次连接的可变状态 |
| `websocket.app` | `Kui` | 应用实例 |

## 带参数的 WebSocket

WebSocket 处理器支持参数绑定：

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

查询参数可以通过函数风格处理器中的 `Annotated` 提取，或直接使用 `websocket.query_params`。

## WebSocket 路由

使用装饰器或路由对象注册 WebSocket 路由：

```python
# 装饰器
@app.router.websocket("/ws", name="websocket")
async def ws_handler():
    ...

# 路由对象
from kui.asgi import SocketRoute

app.router <<= SocketRoute("/ws", ws_handler, name="websocket")
```

WebSocket 路由也可以使用 `Routes` 分组：

```python
from kui.asgi import Routes, SocketRoute

ws_routes = Routes(
    SocketRoute("/chat", chat_handler),
    SocketRoute("/notifications", notify_handler),
)
app.router <<= "/ws" // ws_routes
```

## WebSocket 中间件

为 WebSocket 路由应用中间件：

```python
app.router <<= SocketRoute("/ws", handler) @ ws_auth_middleware

# 应用级 WebSocket 中间件
app = Kui(socket_middlewares=[ws_logging_middleware])
```
