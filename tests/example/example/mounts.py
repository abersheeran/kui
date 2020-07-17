import os
from indexpy.__version__ import __version__
from indexpy.openapi.application import OpenAPI

from . import app

from wsgi_example import wsgi

app.mount_asgi(
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
)

# set django setting
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "wsgi_example.settings")
app.mount_wsgi("/django", wsgi.application)
