## Processor

In the following text, the callable object used to handle WebSocket requests is referred to as a WebSocket processor.

### Function Processor

At the beginning of a WebSocket processor, you must call `await websocket.accept()`, and when the processor exits, you must call `await websocket.close(CLOSE_CODE)`.

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

### Class Processor

Similar to HTTP class processors, WebSocket class processors can inherit from `kui.asgi.SocketView`.

It has a class attribute: `encoding`, which can have several available values - `"anystr"`, `"text"`, `"bytes"`, `"json"`, determining how the received WebSocket data is parsed. The default value is `anystr`.

It has three methods for regular usage, corresponding to different states of a WebSocket connection:

1. `on_connect()`

    This function is called after a WebSocket connection is established.

    If you override this function, you must explicitly call `await websocket.accept()` within it to accept the connection.

2. `on_receive(data: typing.Any)`

    This function is called when a complete data is received, and the type of `data` is controlled by the class attribute `encoding`.

3. `on_disconnect(close_code: int)`

    This function is called when a WebSocket is about to be closed.

    If you override this function, you must explicitly call `await websocket.close(code=close_code)` within it to close the connection.

!!! notice
    All three functions must be defined as asynchronous functions using `async def`.
