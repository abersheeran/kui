# index.py

Although I've never used PHP, I like its hot-swap mechanism. I expect to use index.py to make Python's Web program deployment easier. 

## Install

```
pip install -U index.py
```

Or get the latest version on Github

```
git clone https://github.com/abersheeran/index.py
sudo python3 setup.py install
```

## How to use

Execute the command `index` under the path where you place your Web program.

## Configuration

### Environment variables

At startup, index automatically reads the configuration from the environment variable that begins with `INDEX_`.

like this

```
INDEX_DEBUG=on
INDEX_ENV=pro
```

### Config file

At the root of your web program, the configuration in config.json will be read when index starts.

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

  `ENV` is an important configuration that allows for the distinction between different configuration environments.
