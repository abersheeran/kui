from __future__ import annotations

from kui.asgi import Routes
from kui.routing.extensions import FileRoutes


def test_empty_fileroutes():
    assert (Routes() + FileRoutes("kui.openapi")) == (
        Routes() + FileRoutes("kui.routing")
    )
