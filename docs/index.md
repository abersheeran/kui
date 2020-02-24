# Index.py

这是一个基于 ASGI 协议的异步 web 框架，由 starlette 提供了大量的 ASGI 实现支持，灵感来自于 PHP。

但 Index 并没有一味的模仿 PHP，做到任何 Python 文件都可以被访问执行——仅仅是某个文件夹下的路由才允许被访问。

同样的，热重载在 Python 中的使用也没有像 PHP 一样，因为 Index 想要更容易地支持更高的 QPS，所以热重载不得不受限于 `importlib.reload`，有了两条限制。

Index.py 在最初是对 PHP 中文件系统映射路由与热重载在 Python 中实现的一个探索，但如今的目标是为了更方便快捷的开发 API。

如果你对本框架后续发展有任何的想法，欢迎点击右上角的图标跳转至 Github 提 issue。
