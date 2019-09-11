## Websocket

Websocket 的处理程序编写与 HTTP 类似，同样使用文件路径映射到 URI 的设计。

稍有不同的是 Websocket 的处理类，需要从 `index.view.SocketView` 继承而来，类名必须是 `Socket`。

它有一个类属性：`encoding`，此属性有三个可用值——`"text"`、`"bytes"`、`"json"`，将决定接收到的 websocket 数据以何种编码被解析。

它有三个方法可用于常规使用，分别对应一个 Websocket 连接的不同状态：

1. `on_connect(websocket: WebSocket)`

    这个函数在一个 websocket 连接被建立后调用，你必须在其中显式的调用 `await websocket.accept()` 来接受 websocket 连接的建立。

2. `on_receive(websocket: WebSocket, data: typing.Any)`

    这个函数在接受一条完整的数据时被调用（你不需要考虑数据帧），`data` 的类型由类属性 `encoding` 控制。

3. `on_disconnect(websocket: WebSocket, close_code: int)`

    这个函数在一个 websocket 即将被关闭时调用，你必须在其中显式的调用 `await websocket.close(code=close_code)` 用以关闭 websocket 连接。

**注意：这三个函数必须都以 `async def` 的方式被定义为异步函数**
