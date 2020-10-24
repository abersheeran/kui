from indexpy.conf import Config, ConfigError, UpperDict


def test_config():
    assert Config() is Config()
    assert isinstance(Config().DEBUG, bool)
    assert isinstance(Config().PORT, int)


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


def test_env():
    config = Config()
    config.update(
        {
            "dev": {"debug": True, "host": "localhost"},
            "pro": {"debug": False, "log_level": "warning"},
            "test": {"log_level": "debug"},
        }
    )

    config.update({"env": "dev"})
    assert config.DEBUG is True
    assert config.HOST == "localhost"
    assert config.LOG_LEVEL == "info"

    config.update({"env": "pro"})
    assert config.DEBUG is False
    assert config.HOST == "127.0.0.1"
    assert config.LOG_LEVEL == "warning"

    config.update({"env": "test"})
    assert config.LOG_LEVEL == "debug"
