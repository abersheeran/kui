## HTTP 中间件

### 基于类的中间件

基于类的中间件可以继承 `indexpy.http.MiddlewareMixin`，有以下三个方法可以重写。

- `process_request(request)`

    此方法在请求被层层传递时调用，可用于修改 `request` 对象以供后续处理使用。必须返回 `None`，否则返回值将作为最终结果并直接终止此次请求。

- `process_response(request, response)`

    此方法在请求被正常处理、已经返回响应对象后调用，它必须返回一个可用的响应对象（一般来说直接返回 `response` 即可）。

- `process_exception(request, exception)`

    此方法在中间件之后的调用链路上出现异常时被调用。当其返回值为 `None` 时，异常会被原样抛出，否则其返回值将作为此次请求的响应值被返回。

!!! notice
    以上函数无论你以何种方式定义，都会在加载时被改造成异步函数，但为了减少不必要的损耗，尽量使用 `async def` 去定义它们——除非在其中使用了含有阻塞 IO 的其他函数，例如 Django ORM, PonyORM 等。

很多时候，对于同一个父 URI，需要有多个中间件去处理。通过指定 `Middleware` 中的 `mounts` 属性，可以为中间件指定子中间件。执行时会先执行父中间件，再执行子中间件。

!!! notice
    子中间件的执行顺序是从左到右。

```python
from indexpy.http import MiddlewareMixin


class ExampleChildMiddleware(MiddlewareMixin):
    async def process_request(self, request):
        print("enter first process request")

    async def process_response(self, request, response):
        print("enter last process response")
        return response


class Middleware(MiddlewareMixin):
    mounts = (ExampleChildMiddleware,)

    async def process_request(self, request):
        print("example base middleware request")

    async def process_response(self, request, response):
        print("example base middleware response")
        return response
```
