# Kuí

Kuí 是一个轻量级 Python Web 框架，基于 [baize](https://baize.aber.sh) 和 [pydantic](https://docs.pydantic.dev/) 构建。支持 **ASGI**（异步）和 **WSGI**（同步）两种模式，API 几乎完全一致。

## 特性

- **基数树路由** — 静态路由通过哈希表匹配，动态路由通过基数树匹配，支持类型化参数（`{id:int}`、`{slug:uuid}` 等）
- **类型安全的参数绑定** — 通过 `Annotated` 和 Pydantic 提取并验证请求参数
- **依赖注入** — 函数级别的依赖注入，支持缓存、清理和嵌套解析
- **OpenAPI 自动生成** — 从代码自动生成 Swagger、ReDoc 和 RapiDoc 文档界面
- **中间件组合** — 支持路由级、分组级和应用级中间件，使用 `@` 运算符
- **基于类的视图** — `HttpView` 和 `SocketView` 用于组织处理器
- **WebSocket 支持** — 完整的 WebSocket 路由和基于类的处理器（仅 ASGI）
- **认证** — 内置 Bearer、Basic 和 API Key 认证，自动生成 OpenAPI 安全方案

## 安装

```bash
pip install kui
```

## 快速开始

=== "ASGI"

    ```python
    from typing_extensions import Annotated
    from kui.asgi import Kui, OpenAPI, HttpRoute, Path, Query

    async def hello():
        """首页"""
        return {"message": "Hello, Kuí!"}

    async def greet(name: Annotated[str, Path()]):
        """按名称问候"""
        return {"message": f"Hello, {name}!"}

    app = Kui(routes=[
        HttpRoute("/", hello),
        HttpRoute("/greet/{name}", greet),
    ])

    # 在 /docs 挂载 OpenAPI 文档
    app.router <<= "/docs" // OpenAPI(
        info={"title": "My API", "version": "1.0.0"},
        template_name="swagger",
    ).routes
    ```

    运行：`uvicorn app:app`

=== "WSGI"

    ```python
    from typing_extensions import Annotated
    from kui.wsgi import Kui, OpenAPI, HttpRoute, Path, Query

    def hello():
        """首页"""
        return {"message": "Hello, Kuí!"}

    def greet(name: Annotated[str, Path()]):
        """按名称问候"""
        return {"message": f"Hello, {name}!"}

    app = Kui(routes=[
        HttpRoute("/", hello),
        HttpRoute("/greet/{name}", greet),
    ])

    # 在 /docs 挂载 OpenAPI 文档
    app.router <<= "/docs" // OpenAPI(
        info={"title": "My API", "version": "1.0.0"},
        template_name="swagger",
    ).routes
    ```

    运行：`gunicorn app:app`

## ASGI vs WSGI

| 特性 | ASGI | WSGI |
|---|---|---|
| 处理器风格 | `async def` | `def` |
| WebSocket | 支持 | 不支持 |
| 生命周期事件 | 支持 | 不支持 |
| `socket_middlewares` | 支持 | 不支持 |
| Server-Sent Events | 支持 | 支持 |
| 其他功能 | 相同 API | 相同 API |

需要异步工作负载、WebSocket 或生命周期事件时选择 ASGI。对于简单的同步应用或成熟的部署环境选择 WSGI。

!!! tip
    本文档所有示例均使用 ASGI（`async def`）。WSGI 模式只需去掉 `async`/`await`，并从 `kui.wsgi` 导入即可。详见 [WSGI 模式](wsgi.md)。

## AI 辅助开发

本项目附带 [Claude Code](https://docs.anthropic.com/en/docs/claude-code) 技能——一个 AI 编码代理可使用的完整 Kuí 框架参考。

安装到你的项目中：

```bash
npx skills add abersheeran/kui
```

然后在 Claude Code 中输入 `/kui-framework` 加载完整的 Kuí API 参考，或者直接编写 Kuí 代码——检测到相关导入时技能会自动激活。

该技能涵盖本文档中的所有功能，每个 API 都附带可运行的代码示例。
