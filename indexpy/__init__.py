import sys
import importlib

from .utils import State
from .applications import Index
from .config import here, Config

__all__ = ["Index", "Config", "g"]

# Current working directory first
sys.path.insert(0, here)

# default app
app = Index()

# global state
g = State()
