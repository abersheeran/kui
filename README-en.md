# index.py

[中文](https://github.com/abersheeran/index.py/tree/master/README.md) | English

[![Github Action Test](https://github.com/abersheeran/index.py/workflows/Test/badge.svg)](https://github.com/abersheeran/index.py/actions?query=workflow%3ATest)
[![Build setup.py](https://github.com/abersheeran/index.py/workflows/Build%20setup.py/badge.svg)](https://github.com/abersheeran/index.py/actions?query=workflow%3A%22Build+setup.py%22)
[![Publish PyPi](https://github.com/abersheeran/index.py/workflows/Publish%20PyPi/badge.svg)](https://github.com/abersheeran/index.py/actions?query=workflow%3A%22Publish+PyPi%22)
[![PyPI](https://img.shields.io/pypi/v/index.py)](https://pypi.org/project/index.py/)
![PyPI - Python Version](https://img.shields.io/pypi/pyversions/index.py)

A high-performance web framework based on the ASGI protocol. [Index.py Documentation](https://abersheeran.github.io/index.py/)

You can also view the [Example](https://github.com/abersheeran/index.py/tree/master/tests/example) to learn how to use it.

- No need to manually bind routing (file system mapping URI)
- Automatically parse requests & generate documents (based on `pydantic`)
- Visual API interface (based on `ReDoc`, optimized for fonts)
- Modern test components (based on `pytest` and `requests`)
- Very simple deployment (based on `uvicorn` and `gunicorn`)
- Mount ASGI/WSGI applications (easier to use than `starlette`)
- Better use of background tasks
- Any available ASGI ecosystem can be used

## Install

```bash
pip install -U index.py
```

or install the latest version from Github (unstable).

```bash
pip install -U git+https://github.com/abersheeran/index.py@setup.py
```
