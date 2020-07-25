## WebSocket 处理器

在下文中，用于处理 WebSocket 请求的可调用对象被称为 WebSocket 处理器。

### 函数处理器

函数接受一个位置参数 `websocket`，它是一个 `indexpy.websocket.request.WebSocket` 对象。在函数的开始，必须调用 `await websocket.accept()`，在函数结束必须调用 `await websocket.close(CLOSE_CODE)`。

```python
async def simple_echo(websocket):
    try:
        await websocket.accept()
        while True:
            message = await websocket.receive_json()
            await websocket.send_json(message)
    finally:
        await websocket.close(1000)
```

### 类处理器

与 HTTP 类处理器类似，WebSocket 类处理器需要从 `indexpy.websocket.SocketView` 继承而来。

它有一个类属性：`encoding`，此属性有三个可用值——`"text"`、`"bytes"`、`"json"`，将决定接收到的 WebSocket 数据以何种编码被解析。默认为 `json`。

它有三个方法可用于常规使用，分别对应一个 WebSocket 连接的不同状态：

1. `on_connect()`

    此函数在一个 websocket 连接被建立后调用。

    如果覆盖了此函数，则必须在其中显式的调用 `await self.websocket.accept()` 来接受连接的建立。

2. `on_receive(data: typing.Any)`

    此函数在接受一条完整的数据时被调用，`data` 的类型由类属性 `encoding` 控制。

3. `on_disconnect(close_code: int)`

    此函数在一个 websocket 即将被关闭时调用。

    如果覆盖了此函数，你必须在其中显式的调用 `await self.websocket.close(code=close_code)` 用以关闭连接。

!!! notice
    这三个函数必须都以 `async def` 的方式被定义为异步函数

## WebSocket 对象

每个 WebSocket 连接都会对应一个 `indexpy.websocket.request.WebSocket` 对象，它拥有一对 `receive`/`send` 函数。但为了方便使用，在此基础上封装了三对 recv/send 函数。

- `receive_byte`/`send_byte`: 接收/发送 `bytes` 类型的数据

- `receive_text`/`send_text`: 接收/发送 `text` 类型的数据

- `receive_json`/`send_json`: 接收/发送 `bytes`/`text` 类型的数据，但以 JSON 格式作为中转。这意味着你可以直接发送/接收任何能被 `json.dumps`/`json.loads` 解析的对象。
