<div align="center">

<img style="max-width:60%;" src="https://raw.githubusercontent.com/abersheeran/index.py/master/docs/img/index-py.png" />

<p>
<a href="https://github.com/abersheeran/index.py/tree/master/README.md">中文</a>
|
English
</p>

<p>
<a href="https://github.com/abersheeran/index.py/actions?query=workflow%3ATest">
<img src="https://github.com/abersheeran/index.py/workflows/Test/badge.svg" alt="Github Action Test" />
</a>

<a href="https://app.codecov.io/gh/abersheeran/index.py/">
<img alt="Codecov" src="https://img.shields.io/codecov/c/github/abersheeran/index.py" />
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

An easy-to-use high-performance asynchronous web framework.

<a href="https://index-py.abersheeran.com">Index.py Documentation</a>

</div>

---

Index.py implements the [ASGI3](http://asgi.readthedocs.io/en/latest/) interface and uses Radix Tree for route lookup. Is [one of the fastest Python web frameworks](https://github.com/the-benchmarker/web-frameworks). All features serve the rapid development of high-performance Web services.

- Flexible and efficient routing system (based on Radix Tree)
- Automatically parse requests & generate documents (based on [pydantic](https://pydantic-docs.helpmanual.io/))
- Visual API interface (based on ReDoc, optimized for fonts)
- Built-in deployment commands (based on uvicorn and gunicorn)
- Mount ASGI/WSGI applications
- Background tasks in process (based on [asyncio](https://docs.python.org/3/library/asyncio.html))
- Any available ASGI ecosystem can be used

## Install

```bash
pip install -U index.py
```

or install the latest version from Github (unstable).

```bash
pip install -U git+https://github.com/abersheeran/index.py@setup.py
```

## Quick start

Write the following code to the `main.py` file, use `pip install index.py uvicorn` to install `uvicorn` and `index.py`, and then execute `index-cli uvicorn main:app` to start an efficient Web service now.

```python
from indexpy import Index
from indexpy.routing import HttpRoute


async def homepage():
    return "hello, index.py"


app = Index(
    routes=[
        HttpRoute("/", homepage),
    ]
)
```
