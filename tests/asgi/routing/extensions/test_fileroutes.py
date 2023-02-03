from __future__ import annotations

from xing.asgi import Routes
from xing.routing.extensions import FileRoutes


def test_empty_fileroutes():
    assert (Routes() + FileRoutes("xing.openapi")) == (
        Routes() + FileRoutes("xing.routing")
    )
