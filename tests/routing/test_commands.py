import pytest

from kui.routing.commands import main


@pytest.mark.parametrize(
    "command, output",
    [
        (
            ["example:app"],
            """\
ANY     / => ./example.py:19
ANY     /message => ./example.py:26
GET     /sources/{filepath} => ./example.py:41
ANY     /docs => ./kui/asgi/openapi.py:16
ANY     /docs/ => ./kui/asgi/openapi.py:19
ANY     /docs/json => ./kui/asgi/openapi.py:22
ANY     /docs/heartbeat => ./kui/asgi/openapi.py:32
""",
        ),
        (
            ["example:app", "--match", "/message"],
            """\
ANY     /message => ./example.py:26
""",
        ),
        (
            ["example:app", "--not-match", "/docs*"],
            """\
ANY     / => ./example.py:19
ANY     /message => ./example.py:26
GET     /sources/{filepath} => ./example.py:41
""",
        ),
    ],
)
def test_main(capsys, command, output):
    main(command)
    captured = capsys.readouterr()
    assert captured.out == output
