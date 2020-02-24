import sys
import logging
import importlib

from .applications import Index
from .config import here, Config

app = Index()
logger = logging.getLogger("index")

sys.path.insert(0, here)

__all__ = ["logger", "Index", "Config"]

# loading preset functions
importlib.import_module("indexpy.preset")
