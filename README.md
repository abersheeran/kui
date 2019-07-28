# index.py

Although I've never used PHP, I like its hot-swap mechanism. I expect to use index.py to make Python's Web program deployment easier.

- [Index.py Document](https://abersheeran.com/index.py/)

## Install

```bash
pip install -U index.py
```

Or get the latest version on Github

```bash
pip install -U git+https://github.com/abersheeran/index.py
```

## Quick use

Make a folder that name is `views` and create `index.py` in it.

Write the following in `index.py`

```python
from index.view import View


class HTTP(View):

    def get(self):
        return "hello world"
```

Execute the command `index-cli dev` in the same directory as `views`.

And then, try to change the content in `index.py`, refresh your browser, the page content will be changed.

Index.py can automatically update your Python file changes to the server, manage your index.py service, maybe you only need one ftp.
