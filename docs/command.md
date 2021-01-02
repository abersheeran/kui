## 内置命令

Index 内置了一些命令方便使用。

### index-cli

`index-cli` 是 `index` 内置的根命令，所有其余命令均为 `index-cli` 的子命令。

### index-cli uvicorn

!!! notice
    此命令需要安装 [uvicorn](https://www.uvicorn.org/)。

使用 uvicorn 启动 Index，例如 `index-cli uvicorn main:app`。

### index-cli gunicorn

#### `index-cli gunicorn start`

!!! notice
    此命令需要安装 [gunicorn](https://gunicorn.org/)。

通过 gunicorn 启动服务、管理进程。可以粗浅的理解为能启动多个进程的 `uvicorn` 命令，只不过由 gunicorn 监视并管理各个 worker 进程的运行。例如 `index-cli gunicorn start main:app`。

```
❯ index-cli gunicorn --help
Usage: index-cli gunicorn start [OPTIONS] [APPLICATION]

  Run gunicorn

Options:
  -w, --workers INTEGER
  -k, --worker-class TEXT
  -d, --daemon
  -c, --configuration FILE
  --help
```

你可以通过 `--workers` 选项指定启动的进程数量，如果没有指定，它默认是 CPU 核心数。

你可以通过 `--worker-class` 选项指定启动的 Worker Class，它默认使用 `uvicorn.workers.UvicornWorker`。

如果使用了 `--daemon` 选项，Index 将在后台运行，运行日志写入项目根目录下的 `log.index` 里。

假如你需要编写更多的 gunicorn 配置，可以使用 `-c` 来指定一个 `.py` 作为配置文件。具体配置详见 [gunicorn 文档](http://docs.gunicorn.org/en/latest/configure.html#configuration-file)。

#### `index-cli gunicorn stop`

当你使用 `index-cli gunicorn start` 在启动了 Index 时，可以在项目根目录下执行此命令去停止 Index。

你想强行

#### `index-cli gunicorn restart`

当你使用 `index-cli gunicorn start` 在启动了 Index 时，可以在项目根目录下执行此命令去重启 Index。

#### `index-cli gunicorn reload`

此命令可令 gunicorn 读取新的配置并重新创建 worker 进程。

在没有配置 gunicorn 使用 prefork 模式的时候，此命令效果与 `restart` 相同。

#### `index-cli gunicorn incr`

增加一个工作进程。

#### `index-cli gunicorn decr`

减少一个工作进程。

## 自定义命令

Index 使用了 [click](https://palletsprojects.com/p/click/) 来提供命令支持。

所以如果需要自定义命令，你只需要在项目根目录下新建一个 `commands.py` 文件，在其中按照 click 的规则编写自己的命令。

### 例子

在项目根目录下的 `commands.py` 里写入以下内容

```python
from indexpy.cli import index_cli


@index_cli.command(help='Custom command')
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
  only-print  Custom command
```
