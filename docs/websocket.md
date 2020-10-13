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

- `receive_bytes`/`send_bytes`: 接收/发送 `bytes` 类型的数据

- `receive_text`/`send_text`: 接收/发送 `text` 类型的数据

- `receive_json`/`send_json`: 接收/发送 `bytes`/`text` 类型的数据，但以 JSON 格式作为中转。这意味着你可以直接发送/接收任何能被 `json.dumps`/`json.loads` 解析的对象。

除此之外，WebSocket 对象还拥有 Request 对象相同的部分属性。

### URL

通过 `request.url` 可以获取到请求路径。该属性是一个类似于字符串的对象，它公开了可以从URL中解析出的所有组件。

例如：`request.url.path`, `request.url.port`, `request.url.scheme`

### Path Parameters

`request.path_params` 是一个字典，包含所有解析出的路径参数。

### Headers

`request.headers` 是一个大小写无关的多值字典(multi-dict)。但通过 `request.headers.keys()`/`request.headers.items()` 取出来的 `key` 均为小写。

### Query Parameters

`request.query_params` 是一个不可变的多值字典(multi-dict)。

例如：`request.query_params['search']`

### Client Address

`request.client` 是一个 `namedtuple`，定义为 `namedtuple("Address", ["host", "port"])`。

获取客户端 hostname 或 IP 地址: `request.client.host`。

获取客户端在当前连接中使用的端口: `request.client.port`。

!!!notice
    元组中任何一个元素都可能为 None。这受限于 ASGI 服务器传递的值。

### Cookies

`request.cookies` 是一个标准字典，定义为 `Dict[str, str]`。

例如：`request.cookies.get('mycookie')`

!!!notice
    你没办法从`request.cookies`里读取到无效的 cookie (RFC2109)

### State

某些情况下需要储存一些额外的自定义信息到 `request` 中，可以使用 `request.state` 用于存储。

```python
request.state.user = User(name="Alice")  # 写

user_name = request.state.user.name  # 读

del request.state.user  # 删
```
