The program must respond to a `index.responses.Response` object or its subclass object.

The list of available Response classes is as follows:

* Response
* HTMLResponse
* PlainTextResponse
* JSONResponse
* RedirectResponse
* StreamingResponse
* FileResponse
* TemplateResponse

But in the [Middleware & View](/view/) example, it's okay to return `dict` directly. Because the `str` and `dict` types of handlers are already built into the Index.

## Custom response handle

Index.py allows custom response types.

The following is the definition of the `dict`:

```python
from index.responses import register_type, JSONResponse


@register_type(dict)
def json_type(*args):
    if len(args) > 3:
        raise ValueError("The response cannot exceed three parameters.")

    # judge status code and headers
    try:
        if not isinstance(args[1], int):
            raise TypeError("The response status code must be integer.")

        if not isinstance(args[2], dict):
            raise TypeError("The response headers must be dictionary.")

    except IndexError:
        pass

    return JSONResponse(*args)

```

This will enable index.py to handle the return of the `str` type, and at the same time handle the returned `headers` and `status code`.

It should be noted that such a function must return a `index.responses.Response` object or its subclass object.
