from click.testing import CliRunner

from indexpy.cli import execute, main


def test_execute():
    assert execute(["uvicorn", "--help"]) == 0


def test_custom_command():
    cli = CliRunner()
    assert cli.invoke(main, ["only-print"]).output == "Custom command\n"
