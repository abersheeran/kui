## After response

参考 starlette 的 `background` 设计，Index 提供了更简单可用的使用方法。

```python
from indexpy.view import View
from indexpy.background import after_response


@after_response
def only_print(message: str) -> None:
    print(message)


class HTTP(View):
    async def get(self):
        """
        welcome page
        """
        only_print("world")
        print("hello")
        return ""
```

得益于 [contextvars](https://docs.python.org/zh-cn/3.7/library/contextvars.html)，你可以在整个 HTTP 请求的周期内的任何位置去调用函数，它们都将在响应成功完成后开始执行。

## Finished response

Index 提供了另一个装饰器 `finished_response`，它的使用与 `after_response` 完全相同。不同的是，`finished_response` 的执行时间节点在此次响应结束后（包括 `after_response` 任务执行完成），无论在此过程中是否引发了错误导致流程提前结束，`finished_response` 都将执行。

粗浅的理解，`after_response` 用于请求被正常处理完成后执行一些任务，一旦处理请求的过程中抛出错误，`after_response` 将不会执行。而 `finished_response` 充当了 `finally` 的角色，无论如何，它都会执行（除非 Index 服务终止）。
