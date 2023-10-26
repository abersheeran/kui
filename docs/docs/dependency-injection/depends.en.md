You can use `Depends(func)` to annotate the callable objects on which the view depends. These objects will be called before the view is invoked, and their return values will be injected into the view's parameters.

!!! tip

    You can also annotate the parameters here, which will recursively call all dependent callable objects and the required injected parameters.

```python
def get_name(name: Annotated[str, Query(...)]):
    return name.lower()


def hello(name: Annotated[str, Depends(get_name)]):
    return f"hello {name}"
```

A special case is when the callable object annotated with `Depends(......)` is a generator function. It will be transformed by [`contextlib`](https://docs.python.org/3/library/contextlib.html), and the `yield` value will be injected into the view, while the cleanup part will be executed after the view function exits (regardless of whether the view function returns normally or raises an exception). This is particularly useful when obtaining resources that need to be cleaned up.

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

!!! tip "Asynchronous Dependencies"

If your dependency is asynchronous, you can also use `Depends(func)` to annotate an asynchronous callable object. However, please note that this can only be used in ASGI mode.

```python
async def get_db_connection():
    connection = ...  # get connection
    try:
        yield connection
    finally:
        await connection.close()
```

## Cache

By default, a dependency function is only called once per request. If you want the dependency function to be recalculated on each call within the same request, you can use `cache=False`.

```python
def get_name(name: Annotated[str, Query(...)]):
    return name.lower()


def hello(name: Annotated[str, Depends(get_name, cache=False)]):
    return f"hello {name}"
```
