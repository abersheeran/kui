import sys
import asyncio
import importlib

from .utils import import_module
from .config import Config
from .core import app

# use IOCP in windows
if sys.platform == 'win32' and (sys.version_info.major >= 3 and sys.version_info.minor >= 7):
    asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())

import_module('commands')
import_module('events')
import_module('responses')

__all__ = [
    'app',
    'Config'
]
