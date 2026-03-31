import functools
from pathlib import Path

from kui.utils.inspect import get_object_filepath, get_raw_handler


def test_get_raw_handler_unwraps_wrapped_function():
    def original():
        pass

    @functools.wraps(original)
    def wrapper():
        pass

    assert get_raw_handler(wrapper) is original


def test_get_raw_handler_returns_unwrapped_function_as_is():
    def func():
        pass

    assert get_raw_handler(func) is func


def test_get_object_filepath_returns_absolute_path_outside_cwd():
    path = get_object_filepath(functools.wraps)

    assert Path(path).is_absolute()
    assert path.endswith("functools.py")
