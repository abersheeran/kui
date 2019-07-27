Although I've never used PHP, I like its hot-swap mechanism. I expect to use index.py to make Python's Web program deployment easier.

Index.py can automatically update your Python file changes to the server. Managing your index.py service, maybe you only need one ftp.

## Install

Index.py requires python version at least 3.6.

```bash
pip install -U index.py
```

Or get the latest version on Github

```bash
pip install -U git+https://github.com/abersheeran/index.py
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

### develop

Execute the command `index-cli dev` in the same directory as `views`.

### deploy

In linux, you can use `index-cli gunicorn start` to start server.

* `-w INT`: The number of worker processes for handling requests. This value is best when it is equal to the number of cores of the CPU.

* `-d`: Increasing this parameter will cause the program to run in the background and redirect the log to the `log.index` in the current directory.

In windows......maybe you can use `index-cli dev` to deploy, it uses asyncio to build the server, performance is not too bad.
