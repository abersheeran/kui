import sys
import logging
import importlib

from .utils import State
from .applications import Index
from .config import here, Config

__all__ = ["logger", "Index", "Config"]

app = Index()
logger = logging.getLogger("indexpy")
# global state
g = State()

sys.path.insert(0, here)
# loading preset functions
importlib.import_module("indexpy.preset")
