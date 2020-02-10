from indexpy.config import Config, ConfigError


def test_config():
    assert Config() is Config()
    assert Config().DEBUG is False
    assert Config().PORT == 4190

    try:
        del Config().DEBUG
    except Exception as e:
        assert isinstance(e, ConfigError)

    try:
        del Config()["DEBUG"]
    except Exception as e:
        assert isinstance(e, ConfigError)

    try:
        Config().DEBUG = True
    except Exception as e:
        assert isinstance(e, ConfigError)
