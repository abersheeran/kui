def test_export_all():
    from kui.asgi import __all__ as asgi_all
    from kui.wsgi import __all__ as wsgi_all

    assert sorted(list(asgi_all)) == sorted(
        ["WebSocket", "websocket", "websocket_var", "SocketView", *wsgi_all]
    )
