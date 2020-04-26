Index 内置的配置类 `indexpy.config.Config` 是一个单例类，你可以在任何地方使用 `Config()`，它们都将返回同一个对象。

所有配置都是大小写无关的，`Config().KEY` 等价于 `Config().Key` 和 `Config().key`。

在 Index 启动时，它将自动从环境变量与项目根目录下 index.yaml / index.yml / index.json 里读取配置。

!!! notice
    在 Index 运行之后更改配置文件或者环境变量并不会触发 Index 的热更新，你只能通过重启来使用新配置启动 Index。

## 环境变量

Index 在启动时将从环境变量里读取 `INDEX_DEBUG` 和 `INDEX_ENV` 两个值.

`INDEX_DEBUG` 的值为 `True` 或者 `on` 则 `DEBUG` 为真，其他任何值都是假。

`INDEX_ENV` 的值可以是任何字符串，它对应 `ENV`。

!!! tip
    环境变量在读取配置文件之后读取，这意味你可以使用环境变量的配置来覆盖配置文件里的配置。

## 配置文件示例

```yaml
# overwrite default value to this program
log_level: "info"
allow_underline: true,
allowed_hosts: ["localhost"]
cors_allow_origins: ["*"]
cors_allow_methods: ["GET"]
cors_allow_credentials: false

# use in development
dev:
    "host": "0.0.0.0"
    "debug": true

# use in production
pro:
    "host": "127.0.0.1"
    "port": "41900"
    "log_level": "warning"
    "hotreload": false

# use in test
test:
    log_level: "debug"
```

## 什么是配置隔离？

同一个项目，不同环境下的部分配置可能不同。Index 内置的配置允许使用 `ENV` 来指定当前使用的配置环境。

以上面的配置文件为例，当 `ENV` 的值为 `"dev"` 时，`Config().DEBUG` 会为 `True`。

当你指定 `ENV` 的值为 `"pro"` 时, 在使用 `Config().DEBUG` 的时候，它将先从 `"pro"` 中查找 `"debug"`（不分大小写）。当没有找到时，继续向上查找。然而这份配置文件并没有在根配置中指定 `"debug"`，所以 `Config().DEBUG` 会使用默认值 `False`。

其他的配置同理。
