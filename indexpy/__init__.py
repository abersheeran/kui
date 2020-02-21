import sys
import logging

from .applications import Index
from .config import here, Config

app = Index()
logger = logging.getLogger("index")

sys.path.insert(0, here)

__all__ = ["logger", "Index", "Config"]
