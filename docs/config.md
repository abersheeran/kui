Index.py 内置的配置类 `index.config.Config` 是一个单例类，你可以在任何地方使用 `Config()`，它们都将返回同一个对象。

所有配置都是大小写无关的，但推荐在程序中使用大写。

在 Index 启动时，它将自动从环境变量与项目根目录下 config.json 里读取配置。

**注意**：在 Index 运行之后更改 config.json 或者环境变量并不会触发 Index 的热更新，你只能通过重启来使用新配置启动 Index。

## 环境变量

Index 在启动时将从环境变量里读取 `INDEX_DEBUG` 和 `INDEX_ENV` 两个值.

`INDEX_DEBUG` 的值为 `True` 或者 `on` 则 `DEBUG` 为真，其他任何值都是假。

`INDEX_ENV` 的值可以是任何字符串，它对应 `ENV`。

**注意**：环境变量在读取配置文件之后读取，这意味你可以使用环境变量的配置来覆盖配置文件里的配置。

## 配置文件

在你的项目根目录下的 config.json 文件，将会在 Index 启动时被读取。

下面是一个配置样例：

```json
{
    "log_level": "info",
    "allow_underline": true,
    "allowed_hosts": [
        "localhost"
    ],
    "cors_settings": {
        "allow_origins": [
            "*"
        ],
        "allow_methods": [
            "GET"
        ],
        "allow_credentials": false
    },
    "dev": {
        "host": "0.0.0.0",
        "debug": true
    },
    "pro": {
        "host": "127.0.0.1",
        "port": "41900",
        "log_level": "warning"
    }
}
```

## 所有可用的配置

### ENV

**默认值:** `"dev"`

`env` 是一个十分重要的配置，它允许自动使用对应环境下的配置。

### DEBUG

**默认值:** `False`

我不认为这个配置需要解释什么。

在环境变量里 `INDEX_DEBUG` 为 `"on"` 或者 `"True"` 时，`DEBUG` 为真。

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

### ALLOWED_HOSTS

**默认值:** `["*"]`

`allowed_hosts` 用于指定 Index 允许被访问的 HOST。

一些例子:

  1. `["*"]`

    允许所有的 HOST 访问

  2. `["example.com", "*example.com"]`

    允许 example.com 以及 example.com 的子域名访问。

  3. `["example.com", "test.com"]`

    允许 example.com 与 test.com 的访问。

### FORCE_SSL

**默认值:** `False`

`force_ssl` 允许 HTTP/WS 强制跳转到 HTTPS/WSS。

### AUTORELOAD

**默认值:** `True`

`autoreload` 为真时，将允许 Index 提供真正的热重载功能。

### ALLOW_UNDERLINE

**默认值:** `False`

由于 Python 的 module 只允许字母、数字与下划线，但 URI 中出现出现下划线是被谷歌不推荐的，所以有了这个配置选项。

当 `allow_underline` 为假时，如果 _ 存在于 URI 中，它将会被自动替换成 - 并且 301 跳转过去。

### CORS_ALLOW_ORIGINS

**默认值:** `()`

在跨域请求中允许的 ORIGIN 列表。

例如： `['https://example.org', 'https://www.example.org']`

你可以使用 `['*']` 来允许所有的 ORIGIN 值。

### CORS_ALLOW_ORIGIN_REGEX

**默认值:** `None`

需要是一个正则表达式字符串，它将用于匹配在跨域请求中允许的 ORIGIN 。

例如：`'https://.*\.example\.org'`

### CORS_ALLOW_METHODS

**默认值:** `("GET",)`

在跨域请求中允许的 HTTP 请求方法列表。

你可以使用 `['*']` 来允许所有的请求方法。

### CORS_ALLOW_HEADERS

**默认值:** `()`

在跨域请求中允许被使用的 header 列表。

你可以使用 `['*']` 来允许所有的 header。`Accept`、`Accept-Language`、`Content-Language` 和 `Content-Type` 在跨域请求中是默认允许的。

### CORS_ALLOW_CREDENTIALS

**默认值:** `False`

允许在跨域请求中携带 cookies。

### CORS_EXPOSE_HEADERS

**默认值:** `()`

指定可供浏览器访问的任何响应头。

### CORS_MAX_AGE

**默认值:** `600`

设置浏览器缓存 CORS 响应的最长时间（单位：秒）。

## 什么是配置隔离？

同一个项目，不同环境下的部分配置可能不同。Index 内置的配置允许使用 `ENV` 来指定当前使用的配置环境。

看下面这个配置文件

```json
{
    "log_level": "info",
    "allow_underline": true,
    "allowed_hosts": [
        "localhost"
    ],
    "cors_allow_origins": [
        "*"
    ],
    "cors_allow_methods": [
        "GET"
    ],
    "cors_allow_credentials": false,
    "dev": {
        "host": "0.0.0.0",
        "debug": true
    },
    "pro": {
        "host": "127.0.0.1",
        "port": "41900",
        "log_level": "warning"
    }
}
```

当 `ENV` 的值为 `"dev"` 时，`Config().DEBUG` 会为 `True`。

当你指定 `ENV` 的值为 `"pro"` 时, 在使用 `Config().DEBUG` 的时候，它将先从 `"pro"` 中查找 `"debug"`（不分大小写）。当没有找到时，继续向上查找。然而这份配置文件并没有在根配置中指定 `"debug"`，所以 `Config().DEBUG` 会使用默认值 `False`。

其他的配置同理。
