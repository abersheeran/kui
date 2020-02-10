import os
from indexpy import app
from indexpy.__version__ import __version__
from indexpy.openapi.application import OpenAPI

from wsgi_example import wsgi

app.mount(
    "/openapi",
    OpenAPI("index.py example", "just a example, power by index.py", __version__),
    "asgi",
)

# set django setting
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "wsgi_example.settings")
app.mount("/django", wsgi.application, "wsgi")
app.mount("/static", wsgi.application, "wsgi")
