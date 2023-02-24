使用 `Depends(func)` 可以标注所依赖的可调用对象，在视图被调用前会调用并将返回值注入到视图的参数中。

!!! tip

    你同样可以在这里进行参数标注，将会递归调用所有依赖的可调用对象以及需要注入的参数。

```python
def get_name(name: Annotated[str, Query(...)]):
    return name.lower()


def hello(name: Annotated[str, Depends(get_name)]):
    return f"hello {name}"
```

比较特殊的是，如果你使用 `Depends(......)` 标注的可调用对象是一个生成器函数，那么它将会被 [`contextlib`](https://docs.python.org/3/library/contextlib.html) 改造，`yield` 值被注入视图中，清理部分在视图函数退出后执行（无论视图函数是正常返回或是抛出异常，均会执行清理过程）。在获取某些需要清理的资源时，这特别有效。

```python
def get_db_connection():
    connection = ...  # get connection
    try:
        yield connection
    finally:
        connection.close()


def get_user(db: Annotated[Connection, Depends(get_db_connection)]):
    ...
```

!!! tip "异步依赖"

    如果你的依赖是异步的，你同样可以使用 `Depends(func)` 标注一个异步可调用对象，但请注意，这只能用在 ASGI 模式下。

    ```python
    async def get_db_connection():
        connection = ...  # get connection
        try:
            yield connection
        finally:
            await connection.close()
    ```

## Cache

默认情况下，同一个依赖函数只会在一次请求里被调用一次。如果想要同一个请求里每次都重新计算依赖函数，你可以使用 `cache=False`。

```python
def get_name(name: Annotated[str, Query(...)]):
    return name.lower()


def hello(name: Annotated[str, Depends(get_name, cache=False)]):
    return f"hello {name}"
```
