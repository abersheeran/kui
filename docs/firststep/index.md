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

## 你好

约定一个目录为项目的根目录，在其中创建 `views/index.py` 文件，将下面的代码写入该文件里。

```python
from indexpy.http import HTTPView


class HTTP(HTTPView):

    def get(self):
        return "你好~"
```

在项目的根目录下，执行命令 `index-cli serve`。

访问 [`http://localhost:4190`](http://localhost:4190) 吧！

## 响应 html

在项目根目录下的 `templates` 文件夹里创建一个 `hi.html` 并写入任意的 html 内容。

访问 [`http://localhost:4190/hi`](http://localhost:4190/hi) 就能看到页面。

## 静态文件

对于 Javascript、CSS、Image 等静态文件，放到项目根目录下的 `static` 里，就可以通过 `http://localhost:4190/static/文件名` 访问了。

## 返回 JSON

最常见的接口返回类型就是 JSON，那么让我们对上面创建的 `index.py` 文件做一点修改：

```python
from indexpy.http import HTTPView


class HTTP(HTTPView):

    def get(self):
        return {"key": "value"}
```

试着重新访问 [`http://localhost:4190`](http://localhost:4190)，如果不出意外，你就能看到 `{"key": "value"}`。
