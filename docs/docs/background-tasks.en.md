# Background Tasks

Background tasks run after the response has been sent to the client. Use them for operations that shouldn't block the response, such as sending emails, updating caches, or logging.

## Usage

Queue tasks via `request.background_tasks`:

```python
from kui.asgi import request

@app.router.http.post("/notify")
async def notify():
    request.background_tasks.append(send_email, to="user@example.com")
    request.background_tasks.append(update_stats, event="notification")
    return {"status": "queued"}

async def send_email(to: str):
    # Send email logic here
    ...

async def update_stats(event: str):
    # Update statistics
    ...
```

`request.background_tasks.append(func, *args, **kwargs)` queues a callable with its arguments.

## Execution Order

Tasks execute sequentially in the order they were appended, after the response is sent.

## Sync and Async

Both sync and async functions are supported:

=== "ASGI"

    ```python
    # Async task
    async def send_email(to: str):
        await smtp.send(to=to, subject="Hello")

    # Sync task (also works in ASGI)
    def log_event(message: str):
        logger.info(message)

    request.background_tasks.append(send_email, to="user@example.com")
    request.background_tasks.append(log_event, message="Email sent")
    ```

=== "WSGI"

    ```python
    # Sync task only
    def send_email(to: str):
        smtp.send(to=to, subject="Hello")

    request.background_tasks.append(send_email, to="user@example.com")
    ```

## Notes

- Background tasks share the same process as the request handler. Long-running tasks can affect server throughput.
- For heavy work, consider offloading to a task queue (Celery, RQ, etc.) instead.
- Background tasks have access to the same application state but not the original request/response objects.
