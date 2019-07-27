## View

In all Python files that you expect to handle HTTP requests, you need to define a class called `HTTP`.

Example:

```python
from index.view import View


class HTTP(View):

    def get(self):
        return templates.TemplateResponse("home.html", {"request": self.request})

    def post(self):
        return {"message": "some error in server"}, 500, {"server": "index.py"}
```

In the class, you can define the following methods to handle the corresponding HTTP request.

1. get
2. post
3. put
4. patch
5. delete
6. head
7. options
8. trace

The `self.request` is the `starlette.requests.Request` object.

## Middleware

Define a class named `Middleware` in any `__init__.py` under views, which will intercept or process any request or response that passes this path.

`Middleware` inherits from `MiddlewareMixin` and there are two methods to override it.

1. `process_request(request)`

    This method must return `None`, otherwise the process will be terminated early.

2. `process_response(request, response)`

    This method must return a response.

### example

Write the following in `views/__init__.py`

```python
from index.middleware import MiddlewareMixin
from index.config import logger


class Middleware(MiddlewareMixin):

    async def process_request(self, request):
        logger.info("enter first process request")

    async def process_response(self, request, response):
        logger.info("enter last process response")
        return response
```

Visit `/index.py` in browser, to see the following information in the console

```text
INFO: enter first process request
INFO: enter last process response
INFO: ('127.0.0.1', 21203) - "GET /index.py HTTP/1.1" 200
```

And then, write the following in `views/about/__init__.py`

```python
from index.middleware import MiddlewareMixin
from index.config import logger


class Middleware(MiddlewareMixin):

    def process_request(self, request):
        logger.info("enter second process request")

    def process_response(self, request, response):
        logger.info("enter second last process response")
        return response
```

Visit `/about/me.py` in browser, to see the following information in the console

```text
INFO: enter first process request
INFO: enter second process request
INFO: enter second last process response
INFO: enter last process response
INFO: ('127.0.0.1', 21223) - "GET /about/me.py HTTP/1.1" 200
```
