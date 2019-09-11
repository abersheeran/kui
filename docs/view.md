## HTTP

在`views`里创建任意合法名称的`.py`文件，并在其中创建名为 `HTTP` 的类，即可使此文件能够处理对应其相对于 `views` 的路径的 HTTP 请求。

但较为特殊的是名为 `index.py` 的文件，它能够处理以 `/` 作为最后一个字符的 URI。

**注意**：由于 Python 规定，模块名称必须由字母、数字与下划线组成，但这种 URI 不友好，所以 Index 会将 URI 中的 `_` 全部替换成 `-` 并做 302 跳转，你可以通过设置 [ALLOW_UNDERLINE](/config/#allow_underline) 为真去关闭此功能。

* 一些例子：

    文件相对路径|文件能处理的URI
    ---|---
    views/index.py|/
    views/about.py|/about
    views/api/create_article.py|/api/create-article
    views/article/index.py|/article/

`HTTP` 的类应从 `index.view.View` 继承而来，你可以定义如下方法去处理对应的 HTTP 请求。

1. get
2. post
3. put
4. patch
5. delete
6. head
7. options
8. trace

这些函数不接受任何参数，但可以使用 `self.request` 去获取此次请求的一些信息，它是一个 `starlette.requests.Request` 对象。详细的属性或方法请查看 [starlette 文档](https://www.starlette.io/requests/#request)。

**注意：这些被用于实际处理 HTTP 请求的函数，无论你以何种方式定义，都会在加载时被改造成异步函数，但为了减少不必要的损耗，尽量使用 `async def` 去定义它们。**
