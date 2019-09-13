## 内置命令

Index 内置了一些命令方便使用。**注意：它们都必须在项目根目录下执行**

### serve

* `index-cli serve`

    能启动一个单进程服务，在安装了 uvloop 的环境下使用 uvloop。否则在 Windows 上它使用 [IOCP](https://docs.python.org/3/library/asyncio-policy.html#asyncio.WindowsProactorEventLoopPolicy)，其他系统上使用 [Selector](https://docs.python.org/3/library/asyncio-policy.html#asyncio.DefaultEventLoopPolicy)。

### gunicorn

* `index-cli gunicorn start`

    通过 [gunicorn](https://gunicorn.org/) 启动服务、管理进程。可以粗浅的理解为能启动多个进程的 `serve` 命令。

        ❯ index-cli gunicorn --help
        Usage: index-cli gunicorn [OPTIONS] METHOD

        deploy by gunicorn

        Options:
        -w, --workers INTEGER
        -d, --daemon
        -c, --configuration TEXT
        --help                    Show this message and exit.

    你可以通过 `--workers` 选项指定启动的进程数量，如果没有指定，它默认是 CPU 核心数。

    如果开启了 `--daemon` 选项，Index 将在后台运行，主进程号会被写入项目根目录下的 `.pid` 中，运行日志则写入项目根目录下的 `log.index` 里。

    假如你需要编写更多的 gunicorn 配置，可以使用 `-c` 来指定一个 `.py` 作为配置文件。详见 [gunicorn 文档](http://docs.gunicorn.org/en/latest/configure.html#configuration-file)

* `index-cli gunicorn stop`

    当你使用 `index-cli gunicorn start -d` 在后台启动了 Index 时，可以在项目根目录下执行此命令去停止 Index。

* `index-cli gunicorn reload`

    当你使用 `index-cli gunicorn start -d` 在后台启动了 Index 时，可以在项目根目录下执行此命令去重启 Index。

    这一般在你更改了配置之后使用，因为 Index 内置了真正的热重载能力，如果只是更新代码，你并不需要重启服务。

### check

* `index-cli check`

    这能遍历你项目里的所有 `.py` 文件，来检查其中是不是出现了不允许的 `import` 方法。至于原因，可以看看[ Python 的热重载](https://abersheeran.com/articles/Python-Reload/)。

    并且它会检查 `views` 中的所有 `.py` 是否拥有 `HTTP`（用于处理 HTTP 请求） 或者 `Socket`（用于处理 WebSocket 请求），并在控制台展示所有无处理能力的文件。**不建议把没有处理功能的文件放在 views 里**。

## 自定义命令

Index 使用了 [click](https://palletsprojects.com/p/click/) 来提供命令支持。

所以如果需要自定义命令，你只需要在项目根目录下新建一个 `commands.py` 文件，在其中按照 click 的规则编写自己的命令。

### 例子

在项目根目录下的 `commands.py` 里写入以下内容

```python
from index.cli import main


@main.command(help='Custom command')
def only_print():
    print('Custom command')
```

然后使用 `index-cli --help` 能看到命令已经被加入了

```
❯ index-cli --help
Usage: index-cli [OPTIONS] COMMAND [ARGS]...

Options:
  --help  Show this message and exit.

Commands:
  check       check .py files in program
  gunicorn    deploy by gunicorn
  only-print  Custom command
  serve       use only uvicorn
```
