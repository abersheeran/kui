from __future__ import annotations

import dataclasses
import inspect
import traceback
from contextlib import asynccontextmanager, nullcontext
from typing import TYPE_CHECKING, Any, AsyncGenerator, Callable, List, Tuple

from baize.typing import Receive, Scope, Send

if TYPE_CHECKING:
    from .applications import Kui


LifespanCallback = Callable[["Kui"], Any]


@dataclasses.dataclass
class Lifespan:
    on_startup: List[LifespanCallback] = dataclasses.field(default_factory=list)
    on_shutdown: List[LifespanCallback] = dataclasses.field(default_factory=list)

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        """
        Handle ASGI lifespan messages, which allows us to manage application
        startup and shutdown events.
        """
        app: Kui = scope["app"]

        message = await receive()
        assert message["type"] == "lifespan.startup"
        try:
            for handler in self.on_startup:
                result = handler(app)
                if inspect.isawaitable(result):
                    await result
        except BaseException:
            msg = traceback.format_exc()
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
        except BaseException:
            msg = traceback.format_exc()
            await send({"type": "lifespan.shutdown.failed", "message": msg})
            raise
        await send({"type": "lifespan.shutdown.complete"})


def asynccontextmanager_lifespan(
    func: Callable[["Kui"], AsyncGenerator[Any, None]],
) -> Tuple[LifespanCallback, LifespanCallback]:
    """
    Convert `asynccontextmanager` function to `on_startup` and `on_shutdown`
    """
    context_manager_func = asynccontextmanager(func)
    context_manager: Any = nullcontext()

    async def on_startup(app: Kui) -> None:
        nonlocal context_manager
        context_manager = context_manager_func(app)
        await context_manager.__aenter__()

    async def on_shutdown(app: Kui) -> None:
        await context_manager.__aexit__(None, None, None)

    return on_startup, on_shutdown
