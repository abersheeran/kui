from .core import app
from .config import Config


# check && import
from .autoreload import checkall
checkall(Config().path)
