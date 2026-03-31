# Templates

Kuí supports [Jinja2](https://jinja.palletsprojects.com/) templates for rendering HTML responses.

## Setup

```python
from kui.asgi import Kui, Jinja2Templates

templates = Jinja2Templates("templates")  # Directory path

app = Kui(templates=templates)
```

`Jinja2Templates` accepts one or more directory paths:

```python
templates = Jinja2Templates("templates", "shared_templates")
```

It also supports package-relative paths using `"package:path"` syntax:

```python
templates = Jinja2Templates("mypackage:templates")
```

## Rendering Templates

Use `TemplateResponse` to render a template:

```python
from kui.asgi import TemplateResponse, request

@app.router.http.get("/")
async def homepage():
    return TemplateResponse(
        "index.html",
        {"request": request, "title": "Home", "items": [1, 2, 3]},
    )
```

The second argument is the template context dictionary. Always include `request` if you need to access request data in the template.

## Template Configuration

`Jinja2Templates` creates a Jinja2 `Environment` with:

- `autoescape=True` — HTML escaping enabled by default
- `FileSystemLoader` or `PackageLoader` depending on path format

Access the underlying Jinja2 environment via the `.env` attribute:

```python
templates.env.globals["app_name"] = "My App"
templates.env.filters["custom_filter"] = my_filter_func
```

## Requirements

Jinja2 must be installed:

```bash
pip install jinja2
```

Kuí checks for Jinja2 availability at import time and disables template support if not found.
