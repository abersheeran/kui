import os

import pytest

from indexpy.test import _convert_path, impl_test

from . import example_path


@pytest.mark.parametrize(
    "source,target",
    [
        ("/", "index.py"),
        ("/::Test", "index.py::Test"),
        ("/::Test::test_get_0", "index.py::Test::test_get_0"),
    ],
)
def test_convert_path(source, target):
    from example import app

    assert _convert_path(app, source) == os.path.join(example_path, "views", target)


def test_impl_test_command():
    impl_test("example:app")
