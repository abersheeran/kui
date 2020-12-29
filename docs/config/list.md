### ENV

**默认值:** `"dev"`

`env` 是一个十分重要的配置，它允许[自动使用对应环境下的配置](./index.md#_3)。

它将读取环境变量里 `INDEX_ENV` 的值，可以但不推荐在配置文件中指定。

### DEBUG

**默认值:** `True`

在环境变量里 `INDEX_DEBUG` 为 `"on"` 或者 `"True"` 时，`DEBUG` 为真；该值同样可以在配置文件中指定。

### APP

**没有默认值**

`app` 允许自定义 `serve`/`gunicorn` 等命令中的默认 `app`。

### LOG_LEVEL

**默认值:** `"info"`

### BIND

**默认值:** `"127.0.0.1:4190"`

`bind` 指定 Index 监听的地址。

### AUTORELOAD

**默认值:** `True`

`autoreload` 为真时，使用 `index-cli serve` 或 `index-cli gunicorn start` 时，将会监听当前的项目修改，自动重启服务。
