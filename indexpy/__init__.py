import sys
import importlib

from .utils import State
from .applications import Index
from .config import here, Config

__all__ = ["Index", "Config", "g"]

# default app
app = Index()

# global state
g = State()

# Current working directory first
sys.path.insert(0, here)

# loading preset functions
importlib.import_module("indexpy.preset")
