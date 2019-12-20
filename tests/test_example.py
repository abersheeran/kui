import os
import sys
import traceback

example = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "example"
)


def test_example():
    os.chdir(example)
    sys.path.insert(0, example)

    from index import app, Config
    from index.utils import get_views

    assert Config().path == example

    for view, path in get_views():
        if not hasattr(view, "Test"):
            continue

        for func in view.Test(app, path).all_test:
            func()
