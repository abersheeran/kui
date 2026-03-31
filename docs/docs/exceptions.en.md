# Exception Handling

## HTTPException

Raise `HTTPException` to return an HTTP error response:

```python
from kui.asgi import HTTPException

@app.router.http.get("/items/{item_id:int}")
async def get_item(item_id: Annotated[int, Path()]):
    item = db.get(item_id)
    if not item:
        raise HTTPException(404)
    return item
```

With custom content and headers:

```python
raise HTTPException(
    403,
    content="Access denied",
    headers={"X-Reason": "insufficient-permissions"},
)
```

## Custom Exception Handlers

Register handlers for specific status codes or exception types:

### Status Code Handlers

```python
@app.exception_handler(404)
async def not_found(exc):
    return {"error": "not found"}, 404

@app.exception_handler(500)
async def server_error(exc):
    return {"error": "internal server error"}, 500
```

### Exception Type Handlers

```python
@app.exception_handler(ValueError)
async def value_error(exc):
    return {"error": str(exc)}, 400

@app.exception_handler(PermissionError)
async def permission_error(exc):
    return {"error": "forbidden"}, 403
```

Exception type handlers use MRO (Method Resolution Order) lookup — a handler for a base exception class also catches subclasses.

### Registration via Constructor

```python
app = Kui(
    exception_handlers={
        404: not_found_handler,
        ValueError: value_error_handler,
    }
)
```

## Validation Errors

When [parameter binding](parameters.md) validation fails, the framework raises `RequestValidationError`:

- **Path parameter** validation errors → `404 Not Found`
- **Query/header/cookie/body** validation errors → `422 Unprocessable Entity`

The default 422 response body:

```json
[
    {
        "loc": ["page"],
        "msg": "Input should be a valid integer, unable to parse string as an integer",
        "type": "int_parsing",
        "in": "query"
    }
]
```

The `"in"` field indicates the parameter location: `"path"`, `"query"`, `"header"`, `"cookie"`, or `"body"`.

### Custom Validation Error Handler

```python
from kui.exceptions import RequestValidationError

@app.exception_handler(RequestValidationError)
async def validation_error(exc: RequestValidationError):
    return {
        "message": "Invalid request parameters",
        "details": exc.errors(),
    }, 422
```

`RequestValidationError` provides:

| Method/Attribute | Description |
|---|---|
| `.errors()` | List of error dicts with `loc`, `msg`, `type`, `in` fields |
| `.json()` | JSON string of errors |
| `.in_` | Parameter location: `"path"`, `"query"`, `"header"`, `"cookie"`, `"body"` |

## Exception Handler Execution

Exception handlers wrap the endpoint handler. When an exception occurs:

1. For `HTTPException`, the framework first checks status code handlers (`_status_handlers`)
2. If no status code handler matches, it looks up exception type handlers (walking the MRO chain)
3. If no handler matches, the exception propagates to the ASGI/WSGI server

Exception handlers receive the exception as the sole argument and should return a response (or a value that can be converted to a response).
