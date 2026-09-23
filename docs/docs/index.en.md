# Kuí

Kuí is a lightweight Python web framework built on [baize](https://baize.aber.sh) and [pydantic](https://docs.pydantic.dev/). It supports both **ASGI** (async) and **WSGI** (sync) modes with a nearly identical API.

## Features

- **Radix Tree Routing** — Hash-table matching for static routes and radix-tree matching for dynamic routes, with typed parameters (`{id:int}`, `{slug:uuid}`, etc.)
- **Type-Safe Parameter Binding** — Extract and validate request parameters via `Annotated` and Pydantic
- **Dependency Injection** — Function-level DI with caching, cleanup, and nested resolution
- **OpenAPI Auto-Generation** — Swagger, ReDoc, and RapiDoc UIs from your code
- **Middleware Composition** — Per-route, per-group, and app-level middleware with `@` operator
- **Class-Based Views** — `HttpView` and `SocketView` for organized handlers
- **WebSocket Support** — Full WebSocket routing and class-based handlers (ASGI)
- **Authentication** — Built-in Bearer, Basic, and API Key auth with OpenAPI security schemes

## Installation

```bash
pip install kui
```

## Quick Start

=== "ASGI"

    ```python
    from typing_extensions import Annotated
    from kui.asgi import Kui, OpenAPI, HttpRoute, Path, Query

    async def hello():
        """Homepage"""
        return {"message": "Hello, Kuí!"}

    async def greet(name: Annotated[str, Path()]):
        """Greet by name"""
        return {"message": f"Hello, {name}!"}

    app = Kui(routes=[
        HttpRoute("/", hello),
        HttpRoute("/greet/{name}", greet),
    ])

    # Mount OpenAPI docs at /docs
    app.router <<= "/docs" // OpenAPI(
        info={"title": "My API", "version": "1.0.0"},
        template_name="swagger",
    ).routes
    ```

    Run with: `uvicorn app:app`

=== "WSGI"

    ```python
    from typing_extensions import Annotated
    from kui.wsgi import Kui, OpenAPI, HttpRoute, Path, Query

    def hello():
        """Homepage"""
        return {"message": "Hello, Kuí!"}

    def greet(name: Annotated[str, Path()]):
        """Greet by name"""
        return {"message": f"Hello, {name}!"}

    app = Kui(routes=[
        HttpRoute("/", hello),
        HttpRoute("/greet/{name}", greet),
    ])

    # Mount OpenAPI docs at /docs
    app.router <<= "/docs" // OpenAPI(
        info={"title": "My API", "version": "1.0.0"},
        template_name="swagger",
    ).routes
    ```

    Run with: `gunicorn app:app`

## ASGI vs WSGI

| Feature | ASGI | WSGI |
|---|---|---|
| Handler style | `async def` | `def` |
| WebSocket | Yes | No |
| Lifespan events | Yes | No |
| `socket_middlewares` | Yes | No |
| Server-Sent Events | Yes | Yes |
| Everything else | Same API | Same API |

Choose ASGI for async workloads, WebSocket, or lifespan events. Choose WSGI for simpler synchronous applications or mature deployment environments.

!!! tip
    All examples in this documentation use ASGI (`async def`). For WSGI, simply remove `async`/`await` and import from `kui.wsgi` instead. See [WSGI Mode](wsgi.md) for details.

## AI-Assisted Development

This project ships a [Claude Code](https://docs.anthropic.com/en/docs/claude-code) skill — a comprehensive Kuí framework reference that AI coding agents can use.

Install it into your project:

```bash
npx skills add abersheeran/kui
```

Then in Claude Code, type `/kui-framework` to load the full Kuí API reference, or just start writing Kuí code — the skill is automatically activated when relevant imports are detected.

The skill covers all the features documented here, with working code examples for every API.
