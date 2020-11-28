### ENV

**默认值:** `"dev"`

`env` 是一个十分重要的配置，它允许[自动使用对应环境下的配置](./index.md#_3)。

它将读取环境变量里 `INDEX_ENV` 的值，可以但不推荐在配置文件中指定。

### DEBUG

**默认值:** `False`

在环境变量里 `INDEX_DEBUG` 为 `"on"` 或者 `"True"` 时，`DEBUG` 为真；该值同样可以在配置文件中指定。

### APP

**没有默认值**

`app` 允许自定义 `serve`/`gunicorn` 等命令中的默认 `app`。

### LOG_LEVEL

**默认值:** `"info"`

`log_level` 有五个可用值, 下面是它与 `logging` 的等级对应表

log_level   | logging
---         | ---
"critical"  | logging.CRITICAL
"error"     | logging.ERROR
"warning"   | logging.WARNING
"info"      | logging.INFO
"debug"     | logging.DEBUG

### HOST

**默认值:** `"127.0.0.1"`

`host` 指定 Index 监听的地址。

### PORT

**默认值:** `4190`

`port` 指定 Index 监听的端口。

### AUTORELOAD

**默认值:** `True`

`autoreload` 为真时，使用 `index-cli serve` 或 `index-cli gunicorn start` 时，将会监听当前的项目修改，自动重启服务。
