from __future__ import annotations

from kui.utils.importer import import_module


def test_import_module():
    assert import_module("sys") is None
