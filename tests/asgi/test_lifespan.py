import pytest

from kui.asgi import Kui
from kui.asgi.lifespan import asynccontextmanager_lifespan


async def run_lifespan(app: Kui):
    messages = iter(
        [
            {"type": "lifespan.startup"},
            {"type": "lifespan.shutdown"},
        ]
    )
    sent = []

    async def receive():
        return next(messages)

    async def send(message):
        sent.append(message)

    await app.lifespan({"type": "lifespan", "app": app}, receive, send)
    return sent


@pytest.mark.asyncio
async def test_asynccontextmanager_lifespan(capsys):
    async def f(app):
        print("startup")
        yield
        print("shutdown")

    with pytest.warns(DeprecationWarning):
        on_startup, on_shutdown = asynccontextmanager_lifespan(f)

    await on_startup(None)
    captured = capsys.readouterr()
    assert captured.out == "startup\n"

    await on_shutdown(None)
    captured = capsys.readouterr()
    assert captured.out == "shutdown\n"


@pytest.mark.asyncio
async def test_lifespan_async_generator_is_primary_api():
    events = []

    async def lifespan(app):
        events.append(("lifespan.startup", app))
        yield
        events.append(("lifespan.shutdown", app))

    app = Kui(lifespan=lifespan)

    with pytest.warns(DeprecationWarning):

        @app.on_startup
        async def startup(app):
            events.append(("startup", app))

    with pytest.warns(DeprecationWarning):

        @app.on_shutdown
        async def shutdown(app):
            events.append(("shutdown", app))

    sent = await run_lifespan(app)

    assert [message["type"] for message in sent] == [
        "lifespan.startup.complete",
        "lifespan.shutdown.complete",
    ]
    assert [name for name, _ in events] == [
        "lifespan.startup",
        "startup",
        "shutdown",
        "lifespan.shutdown",
    ]
    assert all(current_app is app for _, current_app in events)


@pytest.mark.asyncio
async def test_on_startup_on_shutdown_still_work_with_warning():
    events = []

    async def startup(app):
        events.append(("startup", app))

    async def shutdown(app):
        events.append(("shutdown", app))

    with pytest.warns(DeprecationWarning):
        app = Kui(on_startup=[startup], on_shutdown=[shutdown])

    sent = await run_lifespan(app)

    assert [message["type"] for message in sent] == [
        "lifespan.startup.complete",
        "lifespan.shutdown.complete",
    ]
    assert [name for name, _ in events] == ["startup", "shutdown"]
    assert all(current_app is app for _, current_app in events)


def test_cannot_mix_lifespan_and_legacy_callbacks():
    async def lifespan(app):
        yield

    async def startup(app):
        return None

    with pytest.warns(DeprecationWarning):
        with pytest.raises(ValueError, match="Cannot use lifespan"):
            Kui(lifespan=lifespan, on_startup=[startup])
