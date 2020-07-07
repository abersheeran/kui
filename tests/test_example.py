import pytest
from click.testing import CliRunner, Result

from indexpy.cli import main, cmd_test


def test_custom_command():
    cli = CliRunner()
    assert cli.invoke(main, ["only-print"]).output == "Custom command\n"
