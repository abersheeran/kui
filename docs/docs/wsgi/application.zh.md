## 初始化参数

除去本文档其他地方提到的参数外，`Kui` 还支持以下初始化参数。

### `http_middlewares`

此参数用于添加全局 HTTP 中间件。

### `factory_class`

此参数用于自定义 HttpRequest 类。

```python
from kui.wsgi import Kui, HttpRequest


class CustomHttpRequest(HttpRequest):
    ...


app = Kui(
    factory_class=FactoryClass(http=CustomHttpRequest),
)
```

### `json_encoder`

此参数用于自定义 JSON 编码器。

```python
from kui.wsgi import Kui
from typedmongo import Table

app = Kui(json_encoder={
    Table: lambda table: table.dump(),
})
```

## 属性

### `state`

`app.state` 用于存储全局变量。

### `should_exit`

`app.should_exit` 用于指示 Application 是否将被关闭。

!!! notice
    该属性需要启动的服务器支持。
