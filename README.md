<div align="center">

<img src="https://raw.githubusercontent.com/abersheeran/index.py/master/docs/img/index-py.png" />

<p>
中文
|
<a href="https://github.com/abersheeran/index.py/tree/master/README-en.md">English</a>
</p>

<p>
<a href="https://github.com/abersheeran/index.py/actions?query=workflow%3ATest">
<img src="https://github.com/abersheeran/index.py/workflows/Test/badge.svg" alt="Github Action Test" />
</a>

<a href="https://app.codecov.io/gh/abersheeran/index.py/">
<img alt="Codecov" src="https://img.shields.io/codecov/c/github/abersheeran/index.py">
</a>
</p>

<p>
<a href="https://github.com/abersheeran/index.py/actions?query=workflow%3A%22Publish+PyPi%22">
<img src="https://github.com/abersheeran/index.py/workflows/Publish%20PyPi/badge.svg" alt="Publish PyPi" />
</a>

<a href="https://pypi.org/project/index.py/">
<img src="https://img.shields.io/pypi/v/index.py" alt="PyPI" />
</a>

<a href="https://pepy.tech/project/index-py">
<img src="https://static.pepy.tech/personalized-badge/index-py?period=total&units=international_system&left_color=black&right_color=blue&left_text=PyPi%20Downloads" alt="Downloads">
</a>
</p>

<p>
<img src="https://img.shields.io/pypi/pyversions/index.py" alt="PyPI - Python Version" />
</p>

一个易用的高性能异步 web 框架。

<a href="https://index-py.aber.sh/stable/">Index.py 文档</a>

</div>

---

Index.py 实现了 [ASGI3](http://asgi.readthedocs.io/en/latest/) 接口，并使用 Radix Tree 进行路由查找。是[最快的 Python web 框架之一](https://github.com/the-benchmarker/web-frameworks)。一切特性都服务于快速开发高性能的 Web 服务。

- 大量正确的类型注释
- 灵活且高效的路由系统
- 可视化 API 接口与在线调试
- 支持 [Server-sent events](https://developer.mozilla.org/zh-CN/docs/Web/API/Server-sent_events/Using_server-sent_events) 与 WebSocket
- 自带一键部署命令 (基于 uvicorn 与 gunicorn)
- 可使用任何可用的 ASGI 生态

## Install

```bash
pip install -U index.py
```

或者直接从 Github 上安装最新版本（不稳定）

```bash
pip install -U git+https://github.com/abersheeran/index.py@setup.py
```

中国大陆内的用户可从 Gitee 上的镜像仓库拉取

```bash
pip install -U git+https://gitee.com/abersheeran/index.py.git@setup.py
```
