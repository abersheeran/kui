# Index.py

这是一个基于 ASGI 协议的异步 web 框架，感谢 PHP 带来的灵感。设计目的在于快速的构建需要的 web 服务，无论是 Templates 还是 API。

单纯看性能，Index.py 不逊色于 Starlette/FastAPI，从理论上 Index.py 更快一点，这是由于前者的路由系统需要遍历搜索到最合适的路由进行处理，而 Index.py 基于文件系统。路由规则越多，Index.py 优势越明显。

Index.py 有如下特性：

- 无需手动绑定路由 (文件系统映射 URI)
- 自动解析请求 & 生成文档 (基于 pydantic)
- 可视化 API 接口 (基于 ReDoc, 针对中文字体优化)
- 现代化的测试组件 (基于 pytest 与 requests)
- 非常简单的部署 (基于 uvicorn 与 gunicorn)
- 支持真正的热重载 (默认关闭)
- 挂载 ASGI/WSGI 应用 (基于 a2wsgi)
- 更好用的 background tasks (基于 starlette)
- 可使用任何可用的 ASGI 生态

Index.py 将始终坚持文件映射路由——如果你喜欢基于装饰器的路由注册（例如 flask），那么请使用 [FastAPI](https://fastapi.tiangolo.com/)，它与 Index.py 都实现了 OpenAPI 文档生成功能、后台任务等功能；如果你喜欢 Django 式的路由注册，可以直接使用 [Starlette](https://starlette.io)，FastAPI 与 Index.py 都是基于 Starlette 的二次开发框架，Index.py 也为其贡献了代码。

**Index.py 功能和 FastAPI 很像，但并没有抄袭 FastAPI，双方属于同时期项目。**只不过 Index.py 并不国际化，所以开发者始终只有我，没有 FastAPI 火热罢了。

如果你对本框架后续发展有任何的想法，欢迎访问 [Github](https://github.com/abersheeran/index.py) 提 issue。
