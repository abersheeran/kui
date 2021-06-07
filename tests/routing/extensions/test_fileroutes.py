from indexpy import Routes
from indexpy.routing.extensions import FileRoutes


def test_empty_fileroutes():
    assert (Routes() + FileRoutes("indexpy.openapi")) == (
        Routes() + FileRoutes("indexpy.routing")
    )
