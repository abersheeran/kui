<div align="center">

<h1> index.py </h1>

<p>
中文
|
<a href="https://github.com/abersheeran/index.py/tree/master/README-en.md">English</a>
</p>

<p>
<a href="https://github.com/abersheeran/index.py/actions?query=workflow%3ATest">
<img src="https://github.com/abersheeran/index.py/workflows/Test/badge.svg" alt="Github Action Test" />
</a>

<a href="https://github.com/abersheeran/index.py/actions?query=workflow%3A%22Build+setup.py%22">
<img src="https://github.com/abersheeran/index.py/workflows/Build%20setup.py/badge.svg" alt="Build setup.py" />
</a>
</p>

<p>
<a href="https://github.com/abersheeran/index.py/actions?query=workflow%3A%22Publish+PyPi%22">
<img src="https://github.com/abersheeran/index.py/workflows/Publish%20PyPi/badge.svg" alt="Publish PyPi" />
</a>

<a href="https://pypi.org/project/index.py/">
<img src="https://img.shields.io/pypi/v/index.py" alt="PyPI" />
</a>
</p>

<p>
<img src="https://img.shields.io/pypi/pyversions/index.py" alt="PyPI - Python Version" />
</p>

一个基于 Radix Tree 的高性能 web 框架。

<a href="https://index-py.abersheeran.com">Index.py 文档</a>

</div>

---

- 灵活且高效的路由系统 (基于 Radix Tree)
- 自动解析请求 & 生成文档 (基于 `pydantic`)
- 可视化 API 接口 (基于 `ReDoc`, 针对中文字体优化)
- 非常简单的部署 (基于 `uvicorn` 与 `gunicorn`)
- 挂载 ASGI/WSGI 应用 (基于 [a2wsgi](https://github.com/abersheeran/a2wsgi/))
- 进程内后台任务 (基于 `asyncio`)
- 可使用任何可用的 ASGI 生态

## Install

```bash
pip install -U index.py
```

或者直接从 Github 上安装最新版本（不稳定）

```bash
pip install -U git+https://github.com/abersheeran/index.py@setup.py
```
