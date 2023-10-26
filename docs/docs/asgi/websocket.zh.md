## 处理器

在下文中，用于处理 WebSocket 请求的可调用对象被称为 WebSocket 处理器。

### 函数处理器

在 WebSocket 处理器的开始，必须调用 `await websocket.accept()`，在处理器退出时必须调用 `await websocket.close(CLOSE_CODE)`。

```python
from kui.asgi import websocket


async def simple_echo():
    await websocket.accept()
    try:
        while True:
            message = await websocket.receive_json()
            await websocket.send_json(message)
    finally:
        await websocket.close(1000)
```

### 类处理器

与 HTTP 类处理器类似，WebSocket 类处理器可以从 `kui.asgi.SocketView` 继承而来。

它有一个类属性：`encoding`，此属性有几个可用值——`"anystr"`、`"text"`、`"bytes"`、`"json"`，将决定接收到的 WebSocket 数据以何种编码被解析。默认为 `anystr`。

它有三个方法可用于常规使用，分别对应一个 WebSocket 连接的不同状态：

1. `on_connect()`

    此函数在一个 websocket 连接被建立后调用。

    如果覆盖了此函数，则必须在其中显式的调用 `await websocket.accept()` 来接受连接的建立。

2. `on_receive(data: typing.Any)`

    此函数在接受一条完整的数据时被调用，`data` 的类型由类属性 `encoding` 控制。

3. `on_disconnect(close_code: int)`

    此函数在一个 websocket 即将被关闭时调用。

    如果覆盖了此函数，你必须在其中显式的调用 `await websocket.close(code=close_code)` 用以关闭连接。

!!! notice
    这三个函数必须都以 `async def` 的方式被定义为异步函数

## WebSocket 对象

每个 WebSocket 连接都会对应一个 `kui.asgi.WebSocket` 对象，它拥有一对 `receive`/`send` 函数。但为了方便使用，在此基础上封装了三对 recv/send 函数。

- `receive_bytes`/`send_bytes`: 接收/发送 `bytes` 类型的数据

- `receive_text`/`send_text`: 接收/发送 `text` 类型的数据

- `receive_json`/`send_json`: 接收/发送 `bytes`/`text` 类型的数据，但以 JSON 格式作为中转。这意味着你可以直接发送/接收任何能被 `json.dumps`/`json.loads` 解析的对象。

除此之外，WebSocket 对象还拥有 HttpRequest 对象部分相同的属性。

### URL

通过 `websocket.url` 可以获取到请求路径。该属性是一个类似于字符串的对象，它公开了可以从URL中解析出的所有组件。

例如：`websocket.url.path`, `websocket.url.port`, `websocket.url.scheme`

### Path Parameters

`websocket.path_params` 是一个字典，包含所有解析出的路径参数。

### Headers

`websocket.headers` 是一个大小写无关的多值字典(multi-dict)。

通过 `websocket.headers.keys()`/`websocket.headers.items()` 取出来的 `key` 均为小写。

### Query Parameters

`websocket.query_params` 是一个多值字典(multi-dict)。

例如：`websocket.query_params['search']`

### Client Address

`websocket.client` 是一个 `namedtuple`，定义为 `namedtuple("Address", ["host", "port"])`。

获取客户端 hostname 或 IP 地址: `websocket.client.host`。

获取客户端在当前连接中使用的端口: `websocket.client.port`。

!!!notice
    元组中任何一个元素都可能为 None。这受限于服务器传递的值。

### Cookies

`websocket.cookies` 是一个标准字典，定义为 `Dict[str, str]`。

例如：`websocket.cookies.get('mycookie')`

### State

某些情况下需要储存一些额外的自定义信息到 `request` 中，可以使用 `websocket.state` 用于存储。

```python
websocket.state.user = User(name="Alice")  # 写

user_name = websocket.state.user.name  # 读

del websocket.state.user  # 删
```

## WebSocket Object

Each WebSocket connection corresponds to a `kui.asgi.WebSocket` object, which has a pair of `receive`/`send` functions. However, for convenience, three pairs of recv/send functions are wrapped on top of them.

- `receive_bytes`/`send_bytes`: Receive/Send data of type `bytes`.

- `receive_text`/`send_text`: Receive/Send data of type `text`.

- `receive_json`/`send_json`: Receive/Send data of type `bytes`/`text`, but using JSON format as an intermediary. This means you can directly send/receive any object that can be parsed by `json.dumps`/`json.loads`.

In addition, the WebSocket object also has some attributes similar to the HttpRequest object.

### URL

You can access the request path through `websocket.url`. This attribute is an object that resembles a string and exposes all the components that can be parsed from the URL.

For example: `websocket.url.path`, `websocket.url.port`, `websocket.url.scheme`

### Path Parameters

`websocket.path_params` is a dictionary that contains all the parsed path parameters.

### Headers

`websocket.headers` is a case-insensitive multi-value dictionary.

The `key` obtained from `websocket.headers.keys()`/`websocket.headers.items()` will be in lowercase.

### Query Parameters

`websocket.query_params` is a multi-value dictionary.

For example: `websocket.query_params['search']`

### Client Address

`websocket.client` is a `namedtuple` defined as `namedtuple("Address", ["host", "port"])`.

To get the client's hostname or IP address: `websocket.client.host`.

To get the port used by the client in the current connection: `websocket.client.port`.

!!!notice
    Any element in the tuple can be None. This depends on the values passed by the server.

### Cookies

`websocket.cookies` is a standard dictionary defined as `Dict[str, str]`.

For example: `websocket.cookies.get('mycookie')`

### State

In some cases, it may be necessary to store additional custom information in the `request`. You can use `websocket.state` for storage.

```python
websocket.state.user = User(name="Alice")  # Write

user_name = websocket.state.user.name  # Read

del websocket.state.user  # Delete
```
