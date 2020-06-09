# index.py

[![Github Action Test](https://github.com/abersheeran/index.py/workflows/Test/badge.svg)](https://github.com/abersheeran/index.py/actions?query=workflow%3ATest)
[![PyPI](https://img.shields.io/pypi/v/index.py)](https://pypi.org/project/index.py/)
![PyPI - Python Version](https://img.shields.io/pypi/pyversions/index.py)

一个基于 ASGI 协议的高性能 web 框架。[Index.py 文档](https://abersheeran.github.io/index.py/)

你也可以直接查看 [Example](https://github.com/abersheeran/index.py/tree/master/example) 来学习如何使用（文档偶尔会滞后一到两天，但 example 被纳入了自动化测试，所以会始终保持最新版）

- 无需手动绑定路由 (文件系统映射URI)
- 自动解析请求 & 生成文档 (基于 pydantic)
- 可视化 API 接口 (基于 ReDoc, 针对中文字体优化)
- 现代化的测试组件 (基于 pytest 与 requests)
- 非常简单的部署 (基于 uvicorn 与 gunicorn)
- 支持真正的热重载
- 挂载 ASGI/WSGI 应用 (比 starlette 更易用)
- 更好用的 background tasks
- 可使用任何可用的 ASGI 生态

## Install

```bash
pip install -U index.py
```

或者直接从 Github 上安装最新版本（不稳定）

```bash
pip install -U git+https://github.com/abersheeran/index.py
```
