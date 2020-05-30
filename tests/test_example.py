import pytest
from click.testing import CliRunner, Result

from indexpy.cli import main, cmd_test


@pytest.fixture
def run():
    cli = CliRunner()

    def cli_run(args) -> Result:
        return cli.invoke(main, args)

    return cli_run


def test_custom_command(run):
    assert run(["only-print"]).output == "Custom command\n"


def test_function(run):
    assert (
        run(["test", "-app", "example:app", "/::Test::test_list_response"]).exit_code
        == 0
    )


def test_url_about(run):
    assert run(["test", "-app", "example:app", "/about/"]).exit_code == 0


def test_url_index(run):
    assert run(["test", "-app", "example:app", "/"]).exit_code == 0
