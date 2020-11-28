Index 允许你使用配置文件来配置 `index-cli serve` / `index-cli gunicorn start` 等命令。在 Python 代码里，你可以使用 `indexpy.conf.serve_config` 读取配置，所有配置都是大小写无关的，`serve_config.KEY` 等价于 `serve_config.Key` 和 `serve_config.key`。

在命令启动时，它将自动从环境变量与项目根目录下 `index.yaml` / `index.yml` / `index.json` 里读取配置。

## 环境变量

Index 在启动时将从环境变量里读取 `INDEX_DEBUG` 和 `INDEX_ENV` 两个值.

`INDEX_DEBUG` 的值为 `True` 或者 `on` 则 `DEBUG` 为真，其他任何值都是假。

`INDEX_ENV` 的值可以是任何字符串，它对应 `ENV`。

!!! tip
    环境变量在读取配置文件之后读取，这意味你可以使用环境变量的配置来覆盖配置文件里的配置。

## 配置文件示例

```yaml
# overwrite default value to this program
app: "example:app"
port: 4918
allowed_hosts: ["localhost"]
cors_allow_origins: ["*"]
cors_allow_methods: ["GET"]
cors_allow_credentials: false

# use in development
dev:
  "host": "localhost"
  "debug": true
  "log_level": "debug"

# use in production
pro:
  "host": "0.0.0.0"
  "port": "41900"
  "log_level": "warning"

# use in test
test:
  log_level: "debug"

```

## 什么是配置隔离？

同一个项目，不同环境下的部分配置可能不同。Index 内置的配置允许使用 `ENV` 来指定当前使用的配置环境。

以上面的配置文件为例，当 `ENV` 的值为 `"dev"` 时，`serve_config.DEBUG` 会为 `True`。

当你指定 `ENV` 的值为 `"pro"` 时, 在使用 `serve_config.DEBUG` 的时候，它将先从 `"pro"` 中查找 `"debug"`（不分大小写）。当没有找到时，继续向上查找。然而这份配置文件并没有在根配置中指定 `"debug"`，所以 `serve_config.DEBUG` 会使用默认值 `False`。

其他的配置同理。
