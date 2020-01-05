## Socket

Websocket 的处理程序编写与 HTTP 类似，同样使用文件路径映射到 URI 的设计。

稍有不同的是 Websocket 的处理类，需要从 `index.view.SocketView` 继承而来，类名必须是 `Socket`。

它有一个类属性：`encoding`，此属性有三个可用值——`"text"`、`"bytes"`、`"json"`，将决定接收到的 websocket 数据以何种编码被解析。

它有三个方法可用于常规使用，分别对应一个 Websocket 连接的不同状态：

1. `on_connect()`

    这个函数在一个 websocket 连接被建立后调用，你必须在其中显式的调用 `await self.websocket.accept()` 来接受 websocket 连接的建立。

2. `on_receive(data: typing.Any)`

    这个函数在接受一条完整的数据时被调用（你不需要考虑数据帧），`data` 的类型由类属性 `encoding` 控制。

3. `on_disconnect(close_code: int)`

    这个函数在一个 websocket 即将被关闭时调用，你必须在其中显式的调用 `await self.websocket.close(code=close_code)` 用以关闭 websocket 连接。

!!! notice
    这三个函数必须都以 `async def` 的方式被定义为异步函数

### WebSocket 对象

每个 websocket 连接都会对应一个 `WebSocket` 对象，它拥有一对 `receive`/`send` 函数。但为了方便使用，在此基础上封装了三对 recv/send 函数。

- `receive_byte`/`send_byte`: 接收/发送 `bytes` 类型的数据

- `receive_text`/`send_text`: 接收/发送 `text` 类型的数据

- `receive_json`/`send_json`: 接收/发送 `bytes`/`text` 类型的数据，但以 JSON 格式作为中转。这意味着你可以直接发送/接收任何能被 `json.dumps`/`json.loads` 解析的对象。
