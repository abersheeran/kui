<div align="center">

<h1> index.py </h1>

<p>
<a href="https://github.com/abersheeran/index.py/tree/master/README.md">中文</a>
|
English
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

<a href="https://pepy.tech/project/index-py/week">
<img src="https://pepy.tech/badge/index-py/week" alt="Week Downloads">
</a>
</p>

<p>
<img src="https://img.shields.io/pypi/pyversions/index.py" alt="PyPI - Python Version" />
</p>

An easy-to-use asynchronous web framework based on Radix Tree.

<a href="https://index-py.abersheeran.com">Index.py Documentation</a>

</div>

---

Index.py implements the [ASGI3](http://asgi.readthedocs.io/en/latest/) interface and uses Radix Tree for route lookup. Is one of the fastest Python web frameworks. All features serve the rapid development of high-performance Web services.

- Flexible and efficient routing system (based on Radix Tree)
- Automatically parse requests & generate documents (based on `pydantic`)
- Visual API interface (based on `ReDoc`, optimized for fonts)
- Modern test components (based on `pytest` and `requests`)
- Very simple deployment (based on `uvicorn` and `gunicorn`)
- Mount ASGI/WSGI applications (easier to use than `starlette`)
- Background tasks in process (based on `asyncio`)
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

Write the following code to a `.py` file and execute it directly, visit `http://127.0.0.1:4190`.

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
