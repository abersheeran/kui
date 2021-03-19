# ![](./img/index-py.png)

这是一个异步 web 框架，设计目的在于快速的构建需要的 web 服务，无论是 Templates 还是 API。

到目前为止，Index.py 不内置数据库、缓存等其他功能。选择困难者请直接使用 [Django](https://www.djangoproject.com/)。

如果你发现了任何的 BUG，欢迎访问 [Github Issues](https://github.com/abersheeran/index.py/issues) 反馈；如果你有需要与其他人共同分享、讨论的事情或希望增加的特性，欢迎访问 [Github Discussions](https://github.com/abersheeran/index.py/discussions) 发起讨论。

## 设计灵感

名称来源于 kennethreitz 的[同名项目](https://github.com/kennethreitz-archive/index.py)，但随着各种想法的发展……逐渐偏离原本的设计。

## 安装方法

Index.py 要求 Python 的版本至少是 3.7，对系统无要求。如果不能/不愿升级 Python 版本，可以使用 docker 来运行 Index.py。

安装 [pypi](https://pypi.org) 上的包

```bash
pip install -U index.py
```

或者直接从 Github 上安装最新版本

```bash
pip install -U git+https://github.com/abersheeran/index.py@setup.py
```

中国大陆内的用户可从 Gitee 上的镜像仓库拉取

```bash
pip install -U git+https://gitee.com/abersheeran/index.py.git@setup.py
```
