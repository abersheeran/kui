尽管我从没使用过PHP编写过任何程序，但我很喜欢它使用文件系统映射到 URI 的设计和它的热重载。

Index.py 让你能够轻松惬意的使用这两个特性，并且还提供了更多的特性。譬如加载时自动异步化，进程内后台任务，任意层级中间件等。

那么，从安装开始吧。

## 安装

Index.py 要求 Python 的版本至少是 3.6。如果不能/不愿升级 Python 版本，可以使用 docker 来运行 Index.py。

安装 [pypi](https://pypi.org) 上的包

```bash
pip install -U index.py
```

或者直接从 Github 上安装最新版本

```bash
pip install -U git+https://github.com/abersheeran/index.py
```

## 第一步

约定一个目录为项目的根目录，在其中创建名为 `views` 的文件夹，在其中创建 `index.py` 文件。

将下面的代码写入 `index.py` 里。

```python
from index.view import View


class HTTP(View):

    def get(self):
        return "hello world"
```

在项目的根目录下，执行命令 `index-cli dev`。

访问 [http://localhost:4190](http://localhost:4190) 吧！
