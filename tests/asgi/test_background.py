import pytest

from kui.asgi.background import BackgroundTask, BackgroundTasks


@pytest.mark.asyncio
async def test_background_task_runs_sync_function():
    calls = []

    task = BackgroundTask(calls.append, "sync")

    await task()

    assert calls == ["sync"]


@pytest.mark.asyncio
async def test_background_task_runs_async_function():
    calls = []

    async def record(value: str) -> None:
        calls.append(value)

    task = BackgroundTask(record, "async")

    await task()

    assert calls == ["async"]


@pytest.mark.asyncio
async def test_background_tasks_execute_in_append_order():
    calls = []
    tasks = BackgroundTasks()

    async def record_async(value: str) -> None:
        calls.append(value)

    tasks.append(calls.append, "first")
    tasks.append(record_async, "second")
    tasks.append(calls.append, "third")

    await tasks()

    assert calls == ["first", "second", "third"]


@pytest.mark.asyncio
async def test_background_tasks_empty_queue_runs_without_error():
    tasks = BackgroundTasks()

    await tasks()


@pytest.mark.asyncio
async def test_background_task_passes_args_and_kwargs():
    calls = []

    def record(*args, **kwargs) -> None:
        calls.append((args, kwargs))

    task = BackgroundTask(record, 1, 2, name="kui")

    await task()

    assert calls == [((1, 2), {"name": "kui"})]
