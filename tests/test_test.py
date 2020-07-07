import os

import pytest

from indexpy.test import _convert_path

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
