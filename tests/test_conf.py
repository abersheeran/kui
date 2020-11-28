import pytest

from indexpy.conf import serve_config, ConfigError, UpperDict


def test_config():
    assert isinstance(serve_config.DEBUG, bool)
    assert isinstance(serve_config.PORT, int)


def test_upper_dict():
    ud = UpperDict({"a": 1, "s": {"a": 2}})
    assert ud["A"] == 1
    assert ud["S"]["A"] == 2


def test_edit():
    with pytest.raises(ConfigError):
        del serve_config.DEBUG

    with pytest.raises(ConfigError):
        del serve_config["DEBUG"]

    with pytest.raises(ConfigError):
        serve_config.DEBUG = True
