## 编写中间件

在 `views` 中任意 `__init__.py` 中定义名为 `Middleware` 的类, 它将能处理所有通过该路径的 HTTP 请求。

譬如在 `views/__init__.py` 中定义的中间件，能处理所有 URI 的 HTTP 请求；在 `views/api/__init__.py` 则只能处理 URI 为 `/api/*` 的请求。

`Middleware` 需要继承 `indexpy.middleware.MiddlewareMixin`，有以下两个方法可以重写。

1. `process_request(request)`

    此方法在请求被层层传递时调用，可用于修改 `request` 对象以供后续处理使用。必须返回 `None`，否则返回值将作为最终结果并直接终止此次请求。

2. `process_response(request, response)`

    此方法在请求被正常处理、已经返回响应对象后调用，它必须返回一个可用的响应对象（一般来说直接返回 `response` 即可）。

!!! notice
    以上函数无论你以何种方式定义，都会在加载时被改造成异步函数，但为了减少不必要的损耗，尽量使用 `async def` 去定义它们。

### 子中间件

很多时候，对于同一个父 URI，需要有多个中间件去处理。通过指定 `Middleware` 中的 `mounts` 属性，可以为中间件指定子中间件。执行时会先执行父中间件，再执行子中间件。

!!! notice
    子中间件的执行顺序是从左到右。

```python
from indexpy.middleware import MiddlewareMixin
from indexpy import logger


class ExampleChildMiddleware(MiddlewareMixin):
    async def process_request(self, request):
        logger.debug("enter first process request")

    async def process_response(self, request, response):
        logger.debug("enter last process response")
        return response


class Middleware(MiddlewareMixin):
    mounts = (ExampleChildMiddleware,)

    async def process_request(self, request):
        logger.debug("example base middleware request")

    async def process_response(self, request, response):
        logger.debug("example base middleware response")
        return response
```
