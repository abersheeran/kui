对于一些故意抛出的异常或者特定的 HTTP 状态码，Index 提供了方法进行统一处理。

以下为样例：

```python
from indexpy import Index
from indexpy.types import Request, Response
from indexpy.http.responses import PlainTextResponse
from starlette.exceptions import HTTPException

app = Index()


@app.exception_handler(404)
def not_found(request: Request, exc: HTTPException) -> Response:
    return PlainTextResponse("what do you want to do?", status_code=404)


@app.exception_handler(ValueError)
def value_error(request: Request, exc: ValueError) -> Response:
    return PlainTextResponse("Something went wrong with the server.", status_code=500)
```

!!!notice
    如果是捕捉 HTTP 状态码，则处理函数的 `exc` 类型是 `starlette.exceptions.HTTPException`。否则，捕捉什么异常，则 `exc` 就是什么类型的异常。
