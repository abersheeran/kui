在传统的多线程 web 开发里，要正常的启动一个后台任务是十分困难的，想想线程安全和变量作用域之类的事情。饶是你经验丰富，解决这些问题依旧是痛苦的。

在 Index-py 中你只需要一些 [`asyncio`](https://docs.python.org/3/library/asyncio.html) 的知识就可以做到轻松的启动后台任务。

## 单一后台任务

很多情况下我们需要这样一种后台任务——在响应结束后，执行某种耗时的 IO 操作。

`indexpy.http.BackgroundTask` 是一个神奇的包装类，它可以帮助你把函数提交到此次 http 响应结束后执行——如果响应未完成就失败了，后台任务将不会执行。

```python
from indexpy import Index
from indexpy.http import Background
from indexpy.http.responses import JSONResponse

app = Index()


async def send_welcome_email(email: str, username: str) -> None:
    ...


@app.router.http("/signup", method="get")
async def signup(request):
    data = await request.json
    username = data['username']
    email = data['email']
    task = BackgroundTask(send_welcome_email, email=email, username=username)
    return JSONResponse({'status': 'Signup successful'}, background=task)
```

## 多后台任务

如果需要顺序的执行多个后台任务(执行顺序由添加顺序决定，先添加、先执行)，需要使用 `BackgroundTasks` 代替 `BackgroundTask`，它们的工作原理是一样的。

```python
from indexpy import Index
from indexpy.http import BackgroundTasks
from indexpy.http.responses import JSONResponse

app = Index()


async def send_welcome_email(to_address):
    ...


async def send_admin_notification(username):
    ...


@app.router.http("/signup", method="get")
    data = await request.json
    username = data['username']
    email = data['email']
    tasks = BackgroundTasks()
    tasks.add_task(send_welcome_email, to_address=email)
    tasks.add_task(send_admin_notification, username=username)
    return JSONResponse({'status': 'Signup successful'}, background=tasks)
```

## 同步任务

以上的用法都仅限于使用 `async def` 定义的异步函数，如果你想在后台运行同步 IO 的任务函数，你应该使用 [`asyncio.loop.run_in_executor`](https://docs.python.org/3/library/asyncio-eventloop.html#asyncio.loop.run_in_executor) 对同步函数进行改造，让它变成一个异步函数。

!!! tip
    在 Python 3.9 与 3.9 以上的版本，你还可以使用 [`asyncio.to_thread`](https://docs.python.org/3/library/asyncio-task.html#asyncio.to_thread) 来改造同步函数，它允许你传递关键词参数，而不是像 [`asyncio.loop.run_in_executor`](https://docs.python.org/3/library/asyncio-eventloop.html#asyncio.loop.run_in_executor) 一样只能传递位置参数。
