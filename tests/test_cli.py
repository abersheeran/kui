from click.testing import CliRunner

from indexpy.cli import main


def test_custom_command():
    @main.command(name="only-print")
    def only_print():
        print("Custom command")

    cli = CliRunner()
    assert cli.invoke(main, ["only-print"]).output == "Custom command\n"
