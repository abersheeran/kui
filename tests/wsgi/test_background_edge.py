from kui.wsgi.background import BackgroundTask, BackgroundTasks


def test_sync_background_task():
    results = []

    def work(value: int) -> None:
        results.append(value)

    task = BackgroundTask(work, 42)

    task()

    assert results == [42]


def test_background_tasks_order():
    results = []
    tasks = BackgroundTasks()

    tasks.append(lambda: results.append("a"))
    tasks.append(lambda: results.append("b"))
    tasks.append(lambda: results.append("c"))

    tasks()

    assert results == ["a", "b", "c"]


def test_background_tasks_empty():
    tasks = BackgroundTasks()

    tasks()


def test_background_task_with_kwargs():
    results = {}

    def work(key: str, value: str = "default") -> None:
        results[key] = value

    task = BackgroundTask(work, "k", value="v")

    task()

    assert results == {"k": "v"}
