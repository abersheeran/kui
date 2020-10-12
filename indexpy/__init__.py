import sys

from .applications import Dispatcher, Index
from .config import Config, here
from .utils import State

__all__ = ["Index", "Dispatcher", "Config", "g"]

# Current working directory first
sys.path.insert(0, here)

# global state
g = State()
