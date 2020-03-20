# index.py

[![Github Action Test](https://github.com/abersheeran/index.py/workflows/Test/badge.svg)](https://github.com/abersheeran/index.py/actions?query=workflow%3ATest)
[![PyPi Downloads](https://pepy.tech/badge/index-py)](https://pepy.tech/project/index-py)
[![PyPi Downloads](https://pepy.tech/badge/index-py/week)](https://pepy.tech/project/index-py/week)

一个基于 ASGI 协议的高性能 web 框架。[Index.py 文档](https://abersheeran.github.io/index.py/)

你也可以直接查看 [Example](https://github.com/abersheeran/index.py/tree/master/example) 来学习如何使用（文档偶尔会滞后一到两天，但 example 被纳入了自动化测试，所以会始终保持最新版）

- 非常简单的部署 (基于 uvicorn 与 gunicorn)
- 支持真正的热重载
- 无需手动绑定路由 (文件系统映射URI)
- 挂载 ASGI/WSGI 应用
- 更好用的 background tasks
- 模型化解析请求 & 自动生成文档 (基于 pydantic)

PHP 对我而言，只有两个优点——URI-文件系统映射和热重载。Index.py 是对这两个特性在 Python 里实现的一个探索。

## Install

```bash
pip install -U index.py
```

或者直接从 Github 上安装最新版本（不稳定）

```bash
pip install -U git+https://github.com/abersheeran/index.py
```

## Hello world

```python
from indexpy.view import View


class HTTP(View):

    def get(self):
        return "hello world"
```
