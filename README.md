<div align="center">

<img style="max-width:60%;" src="https://raw.githubusercontent.com/abersheeran/index.py/master/docs/img/index-py.png" />

<p>
中文
|
<a href="https://github.com/abersheeran/index.py/tree/master/README-en.md">English</a>
</p>

<p>
<a href="https://github.com/abersheeran/index.py/actions?query=workflow%3ATest">
<img src="https://github.com/abersheeran/index.py/workflows/Test/badge.svg" alt="Github Action Test" />
</a>

<a href="https://github.com/abersheeran/index.py/actions?query=workflow%3AOnPush">
<img src="https://github.com/abersheeran/index.py/workflows/OnPush/badge.svg" alt="OnPush" />
</a>
</p>

<p>
<a href="https://github.com/abersheeran/index.py/actions?query=workflow%3A%22Publish+PyPi%22">
<img src="https://github.com/abersheeran/index.py/workflows/Publish%20PyPi/badge.svg" alt="Publish PyPi" />
</a>

<a href="https://pypi.org/project/index.py/">
<img src="https://img.shields.io/pypi/v/index.py" alt="PyPI" />
</a>

<a href="https://pepy.tech/project/index-py/week">
<img src="https://pepy.tech/badge/index-py/week" alt="Week Downloads">
</a>
</p>

<p>
<img src="https://img.shields.io/pypi/pyversions/index.py" alt="PyPI - Python Version" />
</p>

一个基于 Radix Tree 的高性能 web 框架。

<a href="https://index-py.abersheeran.com">Index.py 文档</a>

</div>

---

Index.py 实现了 [ASGI3](http://asgi.readthedocs.io/en/latest/) 接口，并使用 Radix Tree 进行路由查找。是最快的 Python web 框架之一。一切特性都服务于快速开发高性能的 Web 服务。

- 灵活且高效的路由系统 (基于 Radix Tree)
- 自动解析请求 & 生成文档 (基于 [pydantic](https://pydantic-docs.helpmanual.io/))
- 可视化 API 接口 (基于 ReDoc, 针对中文字体优化)
- 自带一键部署命令 (基于 uvicorn 与 gunicorn)
- 挂载 ASGI/WSGI 应用
- 进程内后台任务 (基于 [asyncio](https://docs.python.org/3/library/asyncio.html))
- 可使用任何可用的 ASGI 生态

## Install

```bash
pip install -U index.py
```

或者直接从 Github 上安装最新版本（不稳定）

```bash
pip install -U git+https://github.com/abersheeran/index.py@setup.py
```

中国大陆内的用户可从 Coding 上的镜像仓库拉取

```bash
pip install -U git+https://e.coding.net/aber/github/index.py.git@setup.py
```

## Quick start

向一个 `.py` 文件写入如下代码并直接执行它，访问 `http://127.0.0.1:4190`。

```python
from indexpy import Index


app = Index()


@app.router.http("/", method="get")
async def homepage(request):
    return "hello, index.py"


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, interface="asgi3", port=4190)
```
