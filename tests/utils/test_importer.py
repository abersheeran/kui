from __future__ import annotations

import pytest

from kui.utils.importer import ImportFromStringError, import_from_string, import_module


def test_import_module():
    assert import_module("sys") is None
    assert import_module("kui")


def test_import_from_string():
    assert (
        import_from_string("kui.utils.importer:import_from_string")
        is import_from_string
    )

    with pytest.raises(ImportFromStringError):
        import_from_string("kui.utils.importer")

    with pytest.raises(ImportFromStringError):
        import_from_string("kui.utils.xxxxxxxx:import_from_string")

    with pytest.raises(ImportFromStringError):
        import_from_string("kui.utils.importer:import_from_string:foo")
