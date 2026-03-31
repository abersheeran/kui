from __future__ import annotations

import dataclasses
import inspect
import sys
import traceback
import warnings
from contextlib import asynccontextmanager
from typing import TYPE_CHECKING, Any, AsyncGenerator, Callable, List, Optional, Tuple

from baize.typing import Receive, Scope, Send

if TYPE_CHECKING:
    from .applications import Kui


LifespanCallback = Callable[["Kui"], Any]
LifespanFunc = Callable[["Kui"], AsyncGenerator[Any, None]]


@dataclasses.dataclass
class Lifespan:
    _lifespan: Optional[LifespanFunc] = None
    on_startup: List[LifespanCallback] = dataclasses.field(default_factory=list)
    on_shutdown: List[LifespanCallback] = dataclasses.field(default_factory=list)

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        """
        Handle ASGI lifespan messages, which allows us to manage application
        startup and shutdown events.
        """
        app: Kui = scope["app"]
        context_manager: Any = None
        context_manager_entered = False

        message = await receive()
        assert message["type"] == "lifespan.startup"
        try:
            if self._lifespan is not None:
                context_manager = asynccontextmanager(self._lifespan)(app)
                await context_manager.__aenter__()
                context_manager_entered = True
            for handler in self.on_startup:
                result = handler(app)
                if inspect.isawaitable(result):
                    await result
        except BaseException:
            exc_info = sys.exc_info()
            if context_manager is not None and context_manager_entered:
                await context_manager.__aexit__(*exc_info)
            msg = "".join(traceback.format_exception(*exc_info))
            await send({"type": "lifespan.startup.failed", "message": msg})
            raise
        await send({"type": "lifespan.startup.complete"})

        message = await receive()
        assert message["type"] == "lifespan.shutdown"
        try:
            for handler in self.on_shutdown:
                result = handler(app)
                if inspect.isawaitable(result):
                    await result
            if context_manager is not None:
                await context_manager.__aexit__(None, None, None)
        except BaseException:
            msg = traceback.format_exc()
            await send({"type": "lifespan.shutdown.failed", "message": msg})
            raise
        await send({"type": "lifespan.shutdown.complete"})


def asynccontextmanager_lifespan(
    func: LifespanFunc,
) -> Tuple[LifespanCallback, LifespanCallback]:
    """
    Convert `asynccontextmanager` function to `on_startup` and `on_shutdown`
    """
    warnings.warn(
        "asynccontextmanager_lifespan is deprecated. "
        "Pass the async generator function directly to Kui(lifespan=func).",
        DeprecationWarning,
        stacklevel=2,
    )
    context_manager_func = asynccontextmanager(func)
    context_manager: Any = None

    async def on_startup(app: Kui) -> None:
        nonlocal context_manager
        context_manager = context_manager_func(app)
        await context_manager.__aenter__()

    async def on_shutdown(app: Kui) -> None:
        await context_manager.__aexit__(None, None, None)

    return on_startup, on_shutdown
