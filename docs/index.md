<h1 style="text-align: center;">
<img style="max-width:60%;" src="https://raw.githubusercontent.com/abersheeran/index.py/master/docs/img/index-py.png" />
</h1>

这是一个基于 ASGI 协议的异步 web 框架，设计目的在于快速的构建需要的 web 服务，无论是 Templates 还是 API。

到目前为止，Index.py 不内置数据库、缓存等其他功能。选择困难者请直接使用 [Django](https://www.djangoproject.com/)。

Index.py 有如下特性：

- 灵活且高效的路由系统 (基于 Radix Tree)
- 自动解析请求 & 生成文档 (基于 [pydantic](https://pydantic-docs.helpmanual.io/))
- 可视化 API 接口 (基于 ReDoc, 针对中文字体优化)
- 非常简单的部署 (基于 uvicorn 与 gunicorn)
- 挂载 ASGI/WSGI 应用 (基于 [a2wsgi](https://github.com/abersheeran/a2wsgi/))
- 进程内后台任务 (基于 [asyncio](https://docs.python.org/3/library/asyncio.html))
- 可使用任何可用的 ASGI 生态

Index.py 是率先使用 Radix Tree 进行路由查找的 Python web 框架。并借助 uvicorn 的强力驱动，拥有极高的裸性能。

如果你对本框架后续发展有任何的想法，欢迎访问 [Github](https://github.com/abersheeran/index.py) 提 issue。
