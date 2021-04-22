import asyncio
import threading
from typing import Any


class State(dict):
    """
    An object that can be used to store arbitrary state.
    """

    def __enter__(self):
        if not hasattr(self, "sync_lock"):
            self.sync_lock = threading.Lock()
        self.sync_lock.acquire()
        return self

    def __exit__(self, exc_type, value, traceback):
        self.sync_lock.release()

    async def __aenter__(self):
        if not hasattr(self, "async_lock"):
            self.async_lock = asyncio.Lock()
        await self.async_lock.acquire()
        return self

    async def __aexit__(self, exc_type, value, traceback):
        self.async_lock.release()

    def __setattr__(self, name: Any, value: Any) -> None:
        self[name] = value

    def __getattr__(self, name: Any) -> Any:
        try:
            return self[name]
        except KeyError:
            message = "'{}' object has no attribute '{}'"
            raise AttributeError(message.format(self.__class__.__name__, name))

    def __delattr__(self, name: Any) -> None:
        del self[name]
