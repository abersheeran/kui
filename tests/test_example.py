from click.testing import CliRunner

from indexpy.cli import main


def test_example():
    runner = CliRunner()
    assert runner.invoke(main, ["only-print"]).output == "Custom command\n"


def test_test():
    runner = CliRunner()
    assert (
        runner.invoke(
            main, ["test", "-app", "example:app", "/::Test::test_list_response"]
        ).exit_code
        == 0
    )
    assert (
        runner.invoke(main, ["test", "-app", "example:app", "/about/"]).exit_code == 0
    )
    assert runner.invoke(main, ["test", "-app", "example:app", "/"]).exit_code == 0
    assert runner.invoke(main, ["test", "-app", "example:app"]).exit_code == 0


def test_check():
    runner = CliRunner()
    assert runner.invoke(main, ["check"]).exit_code == 0
