import typing

# WSGI: view PEP3333
Environ = typing.MutableMapping[str, typing.Any]
StartResponse = typing.Callable[[str, typing.Iterable[typing.Tuple[str, str]]], None]
WSGIApp = typing.Callable[
    [Environ, StartResponse], typing.Iterable[typing.Union[str, bytes]]
]
