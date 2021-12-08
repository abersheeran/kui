from hintapi import Routes
from hintapi.routing.extensions import FileRoutes


def test_empty_fileroutes():
    assert (Routes() + FileRoutes("hintapi.openapi")) == (
        Routes() + FileRoutes("hintapi.routing")
    )
