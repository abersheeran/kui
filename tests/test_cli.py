from indexpy.cli import execute


def test_execute():
    assert execute(["uvicorn", "--help"]) == 0

