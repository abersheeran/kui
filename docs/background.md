## 后续任务

（此处称之为后续任务的原因——函数的执行时间点是在 HTTP 响应完成后。）

基于 starlette 的 `background` 设计，Index 提供了更简单可用的使用方法。

```python
from index.view import View
from index.background import after_response


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

得益于 [contextvars](https://docs.python.org/zh-cn/3.7/library/contextvars.html)，你可以在整个 HTTP 请求的周期内的任何位置去调用函数，它们都将在响应完成后开始执行。

这意味着，你可以在 HTTP 中间件中调用被 `after_response` 包裹的函数。
