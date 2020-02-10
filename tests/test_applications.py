from indexpy.applications import Index


def test_create_app():
    assert Index() is Index()
    assert Index(name="test") is Index(name="test")
    assert not Index() is Index(name="test")
