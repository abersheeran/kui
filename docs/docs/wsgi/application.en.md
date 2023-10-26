## Initialization Parameters

In addition to the parameters mentioned elsewhere in this document, `Kui` also supports the following initialization parameters.

### `http_middlewares`

This parameter is used to add global HTTP middlewares.

### `factory_class`

This parameter is used to customize the `HttpRequest` class.

```python
from kui.wsgi import Kui, HttpRequest


class CustomHttpRequest(HttpRequest):
    ...


app = Kui(
    factory_class=FactoryClass(http=CustomHttpRequest),
)
```

## Properties

### `state`

`app.state` is used to store global variables.

### `should_exit`

`app.should_exit` is used to indicate whether the Application should be closed.

!!! notice
    This property requires support from the server being started.
