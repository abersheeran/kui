# ![](./img/index-py.png)

这是一个异步 web 框架，设计目的在于快速的构建需要的 web 服务，无论是 Templates 还是 API。Index.py 是率先使用 Radix Tree 进行路由查找的 Python web 框架。并借助 uvicorn 的强力驱动，拥有极高的裸性能。

到目前为止，Index.py 不内置数据库、缓存等其他功能。选择困难者请直接使用 [Django](https://www.djangoproject.com/)。

如果你对本框架后续发展有任何的想法，欢迎访问 [Github](https://github.com/abersheeran/index.py) 提 issue。

## 设计灵感

名称来源于 kennethreitz 的[同名项目](https://github.com/kennethreitz-archive/index.py)，但随着各种想法的发展……逐渐偏离原本的设计。

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

中国大陆内的用户可从 Coding 上的镜像仓库拉取

```bash
pip install -U git+https://e.coding.net/aber/github/index.py.git@setup.py
```

### 必须依赖

Index.py 并不是一个全然从零开始的框架，它有许多部分依赖于众多优秀的第三方库与 Python 标准库。

- [Starlette](https://www.starlette.io/)：提供了 Request、Response、Background Task、TestClient 等功能。
- [PyYAML](https://github.com/yaml/pyyaml)：为 YAMLResponse 以及配置文件读取提供了 yaml 的读写支持。
- [Jinja2](https://jinja.palletsprojects.com/)：为 TemplateResponse 提供了支持。
- [Python-multipart](https://github.com/andrew-d/python-multipart)：为流式上传文件提供了支持。
- [Pydantic](https://pydantic-docs.helpmanual.io/)：为自动生成 OpenAPI 文档以及请求参数解析提供了支持。
- [Click](https://click.palletsprojects.com/en/7.x/)：为 `index-cli` 命令提供支持。

### 可选依赖

- 如果需要使用 `index-cli serve`，应使用 `pip install -U uvicorn` 安装 [Uvicorn](https://www.uvicorn.org/)。

- 如果需要使用 `index-cli gunicorn`，应使用 `pip install -U uvicorn gunicorn` 安装 [Gunicorn](https://gunicorn.org/)。

- 如果需要使用 `starlette` 的 `TestClient` 用于测试，应使用 `pip install -U index.py[test]` 安装。

但如果你是一个初学者，在学习阶段直接使用 `pip install -U index.py[full]` 安装所有的依赖包即可。
