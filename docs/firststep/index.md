## 安装

Index.py 要求 Python 的版本至少是 3.6，对系统无要求。如果不能/不愿升级 Python 版本，可以使用 docker 来运行 Index.py。

安装 [pypi](https://pypi.org) 上的包

```bash
pip install -U index.py
```

或者直接从 Github 上安装最新版本

```bash
pip install -U git+https://github.com/abersheeran/index.py@setup.py
```

- 如果需要使用 `index-cli serve` 或 `index-cli gunicorn` 命令，应使用 `pip install -U index.py[serve]` 进行安装。

- 如果需要使用 `starlette` 的 `TestClient` 用于测试，应使用 `pip install -U index.py[test]` 进行安装。

但如果你是一个初学者，在学习阶段直接使用 `pip install -U index.py[full]` 安装所有的依赖包即可。

## 你好

创建一个 `main.py` 文件，并写入如下内容。使用 `index-cli serve main:app` 即可启动一个高效的 web 服务。

```python
from indexpy import Index

app = Index()


@app.router.http("/", method="get")
def hi(request):
    return "你好"
```
