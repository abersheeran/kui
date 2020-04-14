import os
from indexpy import app
from indexpy.__version__ import __version__
from indexpy.openapi.application import OpenAPI

from wsgi_example import wsgi, asgi

app.mount(
    "/openapi",
    OpenAPI(
        "index.py example",
        "just a example, power by index.py",
        __version__,
        tags={
            "something": {
                "description": "test over two tags in one path",
                "paths": ["/about/", "/file", "/"],
            },
            "about": {"description": "about page", "paths": ["/about/", "/about/me"]},
            "file": {"description": "get/upload file api", "paths": ["/file"]},
        },
    ),
    "asgi",
)

# set django setting
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "wsgi_example.settings")
app.mount("/django", wsgi.application, "wsgi")
