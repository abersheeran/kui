# index.py

Although I've never used PHP, I like its hot-swap mechanism. I expect to use index.py to make Python's Web program deployment easier.

## Install

```bash
pip install -U index.py
```

Or get the latest version on Github

```bash
git clone https://github.com/abersheeran/index.py
sudo python3 setup.py install
```

## How to use

Execute the command `index-cli dev` under the path where you place your Web program.

### deploy

In linux, you can use `index-cli gunicorn start` to start server.

* `-w INT`: The number of worker processes for handling requests. This value is best when it is equal to the number of cores of the CPU.

* `-d`: Increasing this parameter will cause the program to run in the background and redirect the log to the `log.index` in the current directory.

In windows......maybe you can use `index-cli dev` to deploy, but I don't think it's a good idea.

## Configuration

### Environment variables

At startup, index automatically reads the configuration from the environment variable that begins with `INDEX_`.

like this

```
INDEX_DEBUG=on
INDEX_ENV=pro
```

### Config file

At the root of your web program, the configuration in `config.json` will be read when index starts.

example:

```json
{
  "dev": {
    "debug": true,
  },
  "pro": {
    "debug": false,
    "port": 34567,
    "host": "0.0.0.0"
  }
}
```

### List

* ENV

  **Default: `"dev"`**
  
  `env` is an important configuration that allows for the distinction between different configuration environments.

* DEBUG
  
  **Default: `False`**
  
  Although I don't think this needs explanation.
  
  In the environment variable, INDEX_DEBUG is true when it is on or True, otherwise it is false.

* LOG_LEVEL

  **Default: `"info"`**

  `log_level` has five values, the corresponding table to the `logging` is as follows

  log_level   |loggins
  ---         |---
  "critical"  | logging.CRITICAL
  "error"     | logging.ERROR
  "warning"   | logging.WARNING
  "info"      | logging.INFO
  "debug"     | logging.DEBUG

* HOST

  **Default: `"127.0.0.1"`**
  
  `host` specifies the bound HOST address.

* PORT

  **Default: `4190`**

  `port` pecifies the bound HOST port.

* ALLOWED_HOSTS

  **Default: `["*"]`**
  
  `allowed_hosts` allows you to restrict access to this application's host.

  Some examples:

    - ["*"]

    - ["example.com", "*example.com"]

    - ["example.com", "test.com"]
