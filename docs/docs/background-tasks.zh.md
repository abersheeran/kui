# 后台任务

后台任务在响应发送给客户端之后运行。用于不应阻塞响应的操作，如发送邮件、更新缓存或记录日志。

## 用法

通过 `request.background_tasks` 将任务加入队列：

```python
from kui.asgi import request

@app.router.http.post("/notify")
async def notify():
    request.background_tasks.append(send_email, to="user@example.com")
    request.background_tasks.append(update_stats, event="notification")
    return {"status": "queued"}

async def send_email(to: str):
    # 发送邮件逻辑
    ...

async def update_stats(event: str):
    # 更新统计
    ...
```

`request.background_tasks.append(func, *args, **kwargs)` 将可调用对象及其参数加入队列。

## 执行顺序

任务在响应发送后按添加顺序依次执行。

## 同步与异步

支持同步和异步函数：

=== "ASGI"

    ```python
    # 异步任务
    async def send_email(to: str):
        await smtp.send(to=to, subject="Hello")

    # 同步任务（在 ASGI 中也可以工作）
    def log_event(message: str):
        logger.info(message)

    request.background_tasks.append(send_email, to="user@example.com")
    request.background_tasks.append(log_event, message="Email sent")
    ```

=== "WSGI"

    ```python
    # 仅同步任务
    def send_email(to: str):
        smtp.send(to=to, subject="Hello")

    request.background_tasks.append(send_email, to="user@example.com")
    ```

## 注意事项

- 后台任务与请求处理器在同一进程中执行。长时间运行的任务可能影响服务器吞吐量。
- 对于繁重的工作，建议改用任务队列（Celery、RQ 等）。
- 后台任务可以访问相同的应用状态，但无法访问原始的请求/响应对象。
