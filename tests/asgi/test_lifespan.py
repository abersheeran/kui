import pytest

from kui.asgi.lifespan import asynccontextmanager_lifespan


@pytest.mark.asyncio
async def test_asynccontextmanager_lifespan(capsys):
    async def f(app):
        print("startup")
        yield
        print("shutdown")

    on_startup, on_shutdown = asynccontextmanager_lifespan(f)

    await on_startup(None)
    captured = capsys.readouterr()
    assert captured.out == "startup\n"

    await on_shutdown(None)
    captured = capsys.readouterr()
    assert captured.out == "shutdown\n"
