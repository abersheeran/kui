import sys

from .utils import State
from .applications import Index, Dispatcher
from .config import here, Config

__all__ = ["Index", "Dispatcher", "Config", "g"]

# Current working directory first
sys.path.insert(0, here)

# global state
g = State()
