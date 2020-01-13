## 内置命令

Index 内置了一些命令方便使用。

!!! notice
    它们都必须在项目根目录下执行

### index-cli

`index-cli` 是 `index` 内置的根命令，所有其余命令均为 `index-cli` 的子命令。

`index-cli` 有两个选项——`--env` 与 `--debug / --no-debug`。当你并不想设置，或者无法设置环境变量时，可以使用这两个选项指定 [ENV](/config/#env) 与 [DEBUG](/config/#debug) 配置。在命令中显式的设置这两个配置，可以覆盖环境变量或者配置文件中的值。

以下为一些例子：

```bash
# 设置环境为 pro 并关闭 debug
index-cli --env "pro" --no-debug serve
# 设置环境为 test
index-cli --env "test" test
```

### index-cli serve

* `index-cli serve`

    能启动一个单进程服务，在安装了 uvloop 的环境下使用 uvloop。否则在 Windows 上它使用 [IOCP](https://docs.python.org/3/library/asyncio-policy.html#asyncio.WindowsProactorEventLoopPolicy)，其他系统上使用 [Selector](https://docs.python.org/3/library/asyncio-policy.html#asyncio.DefaultEventLoopPolicy)。

### index-cli gunicorn

* `index-cli gunicorn start`

    通过 [gunicorn](https://gunicorn.org/) 启动服务、管理进程。可以粗浅的理解为能启动多个进程的 `serve` 命令，只不过由 gunicorn 监视并管理各个 worker 进程的运行。

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

### index-cli test

* `index-cli test`

    这个命令用于运行测试，当直接使用 `index-cli test` 时，它将运行所有测试。

    你也可以使用 `index-cli test URI` 来运行某个 URI 路径的测试。

### index-cli check

* `index-cli check`

    这能遍历你项目里的所有 `.py` 文件，来检查其中是不是出现了不允许的 `import` 方法。至于原因，可以看看[ Python 的热重载](https://abersheeran.com/articles/Python-Reload/)。

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
