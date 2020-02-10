import sys
import logging

from .config import Config
from .applications import Index

app = Index()
config = Config()
logger = logging.getLogger("index")

sys.path.insert(0, config.path)

__all__ = ["logger", "Index", "Config"]
