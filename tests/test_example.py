from click.testing import CliRunner

from indexpy.cli import main


def test_custom_command():
    cli = CliRunner()
    assert cli.invoke(main, ["only-print"]).output == "Custom command\n"
