# index.py

中文 | [English](https://github.com/abersheeran/index.py/tree/master/README-en.md)

[![Github Action Test](https://github.com/abersheeran/index.py/workflows/Test/badge.svg)](https://github.com/abersheeran/index.py/actions?query=workflow%3ATest)
[![Build setup.py](https://github.com/abersheeran/index.py/workflows/Build%20setup.py/badge.svg)](https://github.com/abersheeran/index.py/actions?query=workflow%3A%22Build+setup.py%22)
[![Publish PyPi](https://github.com/abersheeran/index.py/workflows/Publish%20PyPi/badge.svg)](https://github.com/abersheeran/index.py/actions?query=workflow%3A%22Publish+PyPi%22)
[![PyPI](https://img.shields.io/pypi/v/index.py)](https://pypi.org/project/index.py/)
![PyPI - Python Version](https://img.shields.io/pypi/pyversions/index.py)

一个基于 ASGI 协议的高性能 web 框架。[Index.py 文档](https://abersheeran.github.io/index.py/)

- 灵活且高效的路由系统 (基于 Radix Tree)
- 自动解析请求 & 生成文档 (基于 `pydantic`)
- 可视化 API 接口 (基于 `ReDoc`, 针对中文字体优化)
- 现代化的测试组件 (基于 `pytest` 与 `requests`)
- 非常简单的部署 (基于 `uvicorn` 与 `gunicorn`)
- 挂载 ASGI/WSGI 应用 (比 `starlette` 更易用)
- 更好用的 background tasks
- 可使用任何可用的 ASGI 生态

## Install

```bash
pip install -U index.py
```

或者直接从 Github 上安装最新版本（不稳定）

```bash
pip install -U git+https://github.com/abersheeran/index.py@setup.py
```
