from click.testing import CliRunner

from indexpy.cli import index_cli


def test_custom_command():
    @index_cli.command(name="only-print")
    def only_print():
        print("Custom command")

    cli = CliRunner()
    assert cli.invoke(index_cli, ["only-print"]).output == "Custom command\n"
