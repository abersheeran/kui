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

    使用 uvicorn 启动 Index.py，如果使用了 Lifespan/Mount 等需要自行创建 application 的功能，应当显式的指定 application，例如 `index-cli serve main:app`。

### index-cli gunicorn

#### `index-cli gunicorn start`

通过 [gunicorn](https://gunicorn.org/) 启动服务、管理进程。可以粗浅的理解为能启动多个进程的 `serve` 命令，只不过由 gunicorn 监视并管理各个 worker 进程的运行。同样的，如果使用了 Lifespan/Mount 等需要自行创建 application 的功能，应当显式的指定 application，例如 `index-cli gunicorn start main:app`。

```
❯ index-cli gunicorn --help
Usage: index-cli gunicorn [OPTIONS] [start|stop|reload] [APPLICATION]

deploy by gunicorn

Options:
-w, --workers INTEGER
-d, --daemon
-c, --configuration FILE
--help                    Show this message and exit.
```

你可以通过 `--workers` 选项指定启动的进程数量，如果没有指定，它默认是 CPU 核心数。

如果开启了 `--daemon` 选项，Index 将在后台运行，主进程号会被写入项目根目录下的 `.pid` 中，运行日志则写入项目根目录下的 `log.index` 里。

假如你需要编写更多的 gunicorn 配置，可以使用 `-c` 来指定一个 `.py` 作为配置文件。详见 [gunicorn 文档](http://docs.gunicorn.org/en/latest/configure.html#configuration-file)

#### `index-cli gunicorn stop`

当你使用 `index-cli gunicorn start -d` 在后台启动了 Index 时，可以在项目根目录下执行此命令去停止 Index。

#### `index-cli gunicorn reload`

当你使用 `index-cli gunicorn start -d` 在后台启动了 Index 时，可以在项目根目录下执行此命令去重启 Index。

### index-cli test

```
❯ index-cli test --help
Usage: index-cli test [OPTIONS] [PATH]

run test

Options:
-app, --application TEXT  ASGI Application, like: main:app
--args TEXT
--help                    Show this message and exit.
```

这个命令用于运行测试，当直接使用 `index-cli test` 时，它将运行所有测试（由 pytest 提供支持）。你可以通过 `--args` 参数传递参数给 pytest，例如：`index-cli test --args "['-q',]"`。

如果使用了 Lifespan/Mount 等需要自行创建 application 的功能，应当显式的指定 application，例如：`index-cli test -app example:app`。

有些时候，也许你并不想执行所有测试，通过 `index-cli test` 的 `PATH` 参数，你可以轻松指定需要执行的测试，以下是一些例子：

* `index-cli test /`: 执行 URL 为 / 的测试
* `index-cli test views/index.py`: 执行 views/index.py 文件中的测试(**与上一条命令等价**)
* `index-cli test /::Test::test_get_0`: 指定一个测试函数
* `index-cli test views/index.py::Test::test_get_0`: 指定一个测试函数(**与上一条命令等价**)

### index-cli check

这能遍历你项目里的所有 `.py` 文件，来检查其中是不是出现了不允许的 `import` 方法。至于原因，可以看看[ Python 的热重载](https://abersheeran.com/articles/Python-Reload/)。

## 自定义命令

Index 使用了 [click](https://palletsprojects.com/p/click/) 来提供命令支持。

所以如果需要自定义命令，你只需要在项目根目录下新建一个 `commands.py` 文件，在其中按照 click 的规则编写自己的命令。

### 例子

在项目根目录下的 `commands.py` 里写入以下内容

```python
from indexpy.cli import main


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
