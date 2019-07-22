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

Make a folder that name is `views` and create `index.py` in it.

Write the following in `index.py`

```python
from index.view import View


class HTTP(View):

    def get(self):
        return "hello world"
```

Execute the command `index-cli dev` in the same directory as `views`.

### deploy

In linux, you can use `index-cli gunicorn start` to start server.

* `-w INT`: The number of worker processes for handling requests. This value is best when it is equal to the number of cores of the CPU.

* `-d`: Increasing this parameter will cause the program to run in the background and redirect the log to the `log.index` in the current directory.

In windows......maybe you can use `index-cli dev` to deploy.

## Configuration

The configuration allows the configuration to be automatically separated by ENV, and lowercase letters in all keys are automatically converted to uppercase.

You can use `Config()` anywhere in the program to use the configuration, which is a class that uses the singleton pattern. Like this

```python
from index import Config

print(Config())
```

### Environment variables

At startup, index automatically reads `INDEX_DEBUG` and `INDEX_ENV` from the environment variable.

Environment variables take precedence over configuration files. This means that you can use environment variables to force the value of `ENV` to be specified.

like this

```bash
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

  I don't think this needs explanation.

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

* ALLOW_UNDERLINE

  **Default: `False`**

  `allow_underline` allows you to determine if an underscore is allowed in the URI by configuring a boolean value. When it is false, if _ exists in the uri, it will be replaced with - and redirected.
  
* CORS_SETTINGS

  **Default:**

    ```python
    {
        "allow_origins": (),
        "allow_methods": ("GET",),
        "allow_headers": (),
        "allow_credentials": False,
        "allow_origin_regex": None,
        "expose_headers": (),
        "max_age": 600,
    }
    ```
    
    The following arguments are supported:

    - allow_origins - A list of origins that should be permitted to make cross-origin requests. 
        
        eg. `['https://example.org', 'https://www.example.org']`. 
        
        You can use ['*'] to allow any origin.
    
    - allow_origin_regex
    
        A regex string to match against origins that should be permitted to make cross-origin requests. 
        
        eg. 'https://.*\.example\.org'.
    
    - allow_methods 
        
        A list of HTTP methods that should be allowed for cross-origin requests. 
        
        You can use ['*'] to allow all standard methods.
    
    - allow_headers
    
        A list of HTTP request headers that should be supported for cross-origin requests. 
        
        You can use ['*'] to allow all headers. The Accept, Accept-Language, Content-Language and Content-Type headers are always allowed for CORS requests.
    
    - allow_credentials
    
        Indicate that cookies should be supported for cross-origin requests. 
    
    - expose_headers
        
        Indicate any response headers that should be made accessible to the browser. 
    
    - max_age 
        
        Sets a maximum time in seconds for browsers to cache CORS responses. 

