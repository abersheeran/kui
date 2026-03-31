import pytest

from kui.asgi import Kui


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
async def test_lifespan_generator_startup_failure_sends_failed_event():
    app = None
    sent = []
    messages = iter([{"type": "lifespan.startup"}])

    async def lifespan(_app):
        raise RuntimeError("startup boom")
        yield

    app = Kui(lifespan=lifespan)

    async def receive():
        return next(messages)

    async def send(message):
        sent.append(message)

    with pytest.raises(RuntimeError, match="startup boom"):
        await app.lifespan({"type": "lifespan", "app": app}, receive, send)

    assert [message["type"] for message in sent] == ["lifespan.startup.failed"]
    assert "startup boom" in sent[0]["message"]


@pytest.mark.asyncio
async def test_lifespan_generator_shutdown_failure_sends_failed_event():
    sent = []
    messages = iter(
        [
            {"type": "lifespan.startup"},
            {"type": "lifespan.shutdown"},
        ]
    )

    async def lifespan(app):
        yield
        raise RuntimeError("shutdown boom")

    app = Kui(lifespan=lifespan)

    async def receive():
        return next(messages)

    async def send(message):
        sent.append(message)

    with pytest.raises(RuntimeError, match="shutdown boom"):
        await app.lifespan({"type": "lifespan", "app": app}, receive, send)

    assert [message["type"] for message in sent] == [
        "lifespan.startup.complete",
        "lifespan.shutdown.failed",
    ]
    assert "shutdown boom" in sent[-1]["message"]


@pytest.mark.asyncio
async def test_sync_on_startup_callback_works_with_deprecation_warning():
    events = []

    def startup(app):
        events.append(app)

    with pytest.warns(DeprecationWarning):
        app = Kui(on_startup=[startup])

    sent = await run_lifespan(app)

    assert [message["type"] for message in sent] == [
        "lifespan.startup.complete",
        "lifespan.shutdown.complete",
    ]
    assert events == [app]
