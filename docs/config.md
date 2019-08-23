## 编写配置

Index.py 内置的配置类 `index.config.Config` 是一个单例类，你可以在任何地方使用 `Config()`，它们都将返回同一个对象。

所有配置都是大小写无关的，但推荐在程序中使用大写——因为所有配置在启动后都只读。

在 Index 启动时，它将自动从环境变量与项目根目录下 config.json 里读取配置。

**注意**：在 Index 运行之后更改 config.json 或者环境变量并不会触发 Index 的热更新，你只能通过重启来使用新配置启动 Index。

### 环境变量

Index 在启动时将从环境变量里读取 `INDEX_DEBUG` 和 `INDEX_ENV` 两个值.

`INDEX_DEBUG` 的值为 `True` 或者 `on` 则 `DEBUG` 为真，其他任何值都是假。

`INDEX_ENV` 的值可以是任何字符串，它对应 `ENV`。

**注意**：环境变量在读取配置文件之后读取，这意味你可以使用环境变量的配置来覆盖配置文件里的配置。

### 配置文件

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

### 所有可用的配置

#### ENV

- **默认值:** `"dev"`

`env` 是一个十分重要的配置，它允许自动使用对应环境下的配置。

#### DEBUG

- **默认值:** `False`

我不认为这个配置需要解释什么。

在环境变量里 `INDEX_DEBUG` 为 `"on"` 或者 `"True"` 时，`DEBUG` 为真。

#### LOG_LEVEL

- **默认值:** `"info"`

`log_level` 有五个可用值, 下面是它与 `logging` 的等级对应表

log_level   | logging
---         | ---
"critical"  | logging.CRITICAL
"error"     | logging.ERROR
"warning"   | logging.WARNING
"info"      | logging.INFO
"debug"     | logging.DEBUG

#### HOST

- **默认值:** `"127.0.0.1"`

`host` 指定 Index 监听的地址。

#### PORT

- **默认值:** `4190`

`port` 指定 Index 监听的端口。

#### ALLOWED_HOSTS

- **默认值:** `["*"]`

`allowed_hosts` 用于指定 Index 允许被访问的 HOST。

一些例子:

  1. `["*"]`

    允许所有的 HOST 访问

  2. `["example.com", "*example.com"]`

    允许 example.com 以及 example.com 的子域名访问。

  3. `["example.com", "test.com"]`

    允许 example.com 与 test.com 的访问。

#### FORCE_SSL

- **默认值:** `False`

`force_ssl` 允许 HTTP/WS 强制跳转到 HTTPS/WSS。

#### ALLOW_UNDERLINE

- **默认值:** `False`

由于 Python 的 module 只允许字母、数字与下划线，但 URI 中出现出现下划线是被谷歌不推荐的，所以有了这个配置选项。

当 `allow_underline` 为假时，如果 _ 存在于 URI 中，它将会被自动替换成 - 并且 301 跳转过去。

#### CORS_SETTINGS

- **默认值:**

  {
    "allow_origins": (),
    "allow_methods": ("GET",),
    "allow_headers": (),
    "allow_credentials": False,
    "allow_origin_regex": None,
    "expose_headers": (),
    "max_age": 600,
  }

The following arguments are supported:

- allow_origins

    A list of origins that should be permitted to make cross-origin requests.

    eg. `['https://example.org', 'https://www.example.org']`.

    You can use `['*']` to allow any origin.

- allow_origin_regex

    A regex string to match against origins that should be permitted to make cross-origin requests.

    eg. `'https://.*\.example\.org'`.

- allow_methods

    A list of HTTP methods that should be allowed for cross-origin requests.

    You can use `['*']` to allow all standard methods.

- allow_headers

    A list of HTTP request headers that should be supported for cross-origin requests.

    You can use `['*']` to allow all headers. The Accept, Accept-Language, Content-Language and Content-Type headers are always allowed for CORS requests.

- allow_credentials

    Indicate that cookies should be supported for cross-origin requests.

- expose_headers

    Indicate any response headers that should be made accessible to the browser.

- max_age

    Sets a maximum time in seconds for browsers to cache CORS responses.

## Explain environmental isolation

Some configurations of the development and production environments may differ when developing a website. Index.py has this isolation built in. You only need to specify the value of INDEX-_ENV in the environment variable. It will first read from the specified environment. If the specified environment does not exist, it will continue to look up.

Like this configuration file

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

`Config().DEBUG` will be `True` when you specify the value of `INDEX_ENV` as "dev".

When you specify the value of `INDEX_ENV` as "pro", when using `Config().DEBUG`, it will first look for "pro". When it is not found, it continues to look up. However, this configuration file does not have `DEBUG` configured on root, so the default value of `False` is used.

Other configurations are also like this.
