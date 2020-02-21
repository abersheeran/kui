from indexpy.config import UpperDict, Config, ConfigError


def test_config():
    assert Config() is Config()
    assert Config().DEBUG is False
    assert Config().PORT == 4190


def test_upper_dict():
    ud = UpperDict({"a": 1, "s": {"a": 2}})
    assert ud["A"] == 1
    assert ud["S"]["A"] == 2


def test_edit():
    try:
        del Config().DEBUG
        assert False
    except Exception as e:
        assert isinstance(e, ConfigError)

    try:
        del Config()["DEBUG"]
        assert False
    except Exception as e:
        assert isinstance(e, ConfigError)

    try:
        Config().DEBUG = True
        assert False
    except Exception as e:
        assert isinstance(e, ConfigError)
