from index import app
from index.__version__ import __version__
from index.openapi.application import OpenAPI

app.mount(
    "/openapi",
    OpenAPI("index.py example", "just a example, power by index.py", __version__),
    "asgi",
)
