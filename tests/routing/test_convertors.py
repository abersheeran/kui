import pytest

from indexpy.routing.convertors import is_compliant


@pytest.mark.parametrize(
    "string, result",
    [
        ("", True),
        ("{}", True),
        ("1{1}1", True),
        ("}{", False),
        ("{}}", False),
        ("}", False),
        ("{{}", False),
        ("{", False),
    ],
)
def test_is_compliant(string, result):
    assert is_compliant(string) == result
