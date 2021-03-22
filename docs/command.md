## 内置命令

Index-py 内置了一些命令方便使用。

### index-cli

`index-cli` 是 `index` 内置的根命令，所有其余命令均为 `index-cli` 的子命令。

### index-cli uvicorn

!!! notice
    此命令需要安装 [uvicorn](https://www.uvicorn.org/)。

```bash
❯ index-cli uvicorn --help
Usage: index-cli uvicorn [OPTIONS] APPLICATION

  use uvicorn to run Index.py application

Options:
  --bind TEXT                     [default: 127.0.0.1:4190]
  --autoreload / --no-autoreload  [default: True]
  --log-level [critical|error|warning|info|debug]
                                  [default: info]
  --help                          Show this message and exit.
```

此命令可以便捷的使用 Uvicorn 启动 Index-py 项目。例如：`index-cli uvicorn main:app`。

有三个选项可以使用：

- `--bind`：指定绑定的地址，例如："0.0.0.0:80"、"unix:./uvicorn.sock"

- `--autoreload / --no-autoreload`：指定 Python 文件变更时，是否自动重启服务。

- `--log-level`：指定输出日志的最低等级。

### index-cli gunicorn

#### `index-cli gunicorn start`

!!! notice
    此命令需要安装 [gunicorn](https://gunicorn.org/)。

通过 gunicorn 启动服务、管理进程。可以粗浅的理解为能启动多个进程的 `uvicorn` 命令，只不过由 gunicorn 监视并管理各个 worker 进程的运行。例如 `index-cli gunicorn start main:app`。

```
❯ index-cli gunicorn start --help
Usage: index-cli gunicorn start [OPTIONS] APPLICATION

  Run gunicorn

Options:
  --bind TEXT                     [default: 127.0.0.1:4190]
  --autoreload / --no-autoreload  [default: False]
  --log-level [critical|error|warning|info|debug]
                                  [default: info]
  -w, --workers INTEGER
  -d, --daemon                    [default: False]
  -c, --configuration FILE
  --help                          Show this message and exit.
```

- `--bind`：指定绑定的地址，例如："0.0.0.0:80"、"unix:./uvicorn.sock"

- `--autoreload / --no-autoreload`：指定 Python 文件变更时，是否自动重启服务。

- `--log-level`：指定输出日志的最低等级。

- `--workers`：指定启动的进程数量，如果没有指定，它默认是 CPU 核心数。

如果使用了 `--daemon` 选项，Index-py 将在后台运行，运行日志写入项目根目录下的 `run.log` 里。

假如你需要编写更多的 gunicorn 配置，可以使用 `-c` 来指定一个 `.py` 作为配置文件。具体配置详见 [gunicorn 文档](http://docs.gunicorn.org/en/latest/configure.html#configuration-file)。

#### `index-cli gunicorn stop`

当你使用 `index-cli gunicorn start` 在启动了 Index-py 时，可以在项目根目录下执行此命令去停止 Index。

你想强行停止，而不等待现存的所有请求结束之后再停止，则可以使用 `--force-stop` 选项。

#### `index-cli gunicorn restart`

当你使用 `index-cli gunicorn start` 在启动了 Index-py 时，可以在项目根目录下执行此命令去重启 Index。

#### `index-cli gunicorn reload`

此命令可令 gunicorn 读取新的配置并重新创建 worker 进程。

在没有配置 gunicorn 使用 prefork 模式的时候，此命令效果与 `restart` 相同。

#### `index-cli gunicorn incr`

增加一个工作进程。

#### `index-cli gunicorn decr`

减少一个工作进程。

## 自定义命令

Index-py 使用了 [click](https://palletsprojects.com/p/click/) 来提供命令支持。

所以如果需要自定义命令，你只需要在项目根目录下新建一个 `commands.py` 文件，在其中按照 click 的规则编写自己的命令。

### 样例

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

### 引入第三方模块命令

在需要使用其他人封装好的第三方模块命令时，只需要在上述的 `commands.py` 文件中编写 `import` 语句导入第三方模块中编写的命令模块即可。

这一设计是为了让用户显式地知悉自己从哪些第三方模块里导入了命令。
