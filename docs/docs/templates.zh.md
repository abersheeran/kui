# 模板

Kuí 支持 [Jinja2](https://jinja.palletsprojects.com/) 模板用于渲染 HTML 响应。

## 配置

```python
from kui.asgi import Kui, Jinja2Templates

templates = Jinja2Templates("templates")  # 目录路径

app = Kui(templates=templates)
```

`Jinja2Templates` 接受一个或多个目录路径：

```python
templates = Jinja2Templates("templates", "shared_templates")
```

也支持使用 `"package:path"` 语法的包相对路径：

```python
templates = Jinja2Templates("mypackage:templates")
```

## 渲染模板

使用 `TemplateResponse` 渲染模板：

```python
from kui.asgi import TemplateResponse, request

@app.router.http.get("/")
async def homepage():
    return TemplateResponse(
        "index.html",
        {"request": request, "title": "首页", "items": [1, 2, 3]},
    )
```

第二个参数是模板上下文字典。如果需要在模板中访问请求数据，请始终包含 `request`。

## 模板配置

`Jinja2Templates` 创建的 Jinja2 `Environment` 具有：

- `autoescape=True` — 默认启用 HTML 转义
- `FileSystemLoader` 或 `PackageLoader`（取决于路径格式）

通过 `.env` 属性访问底层 Jinja2 环境：

```python
templates.env.globals["app_name"] = "My App"
templates.env.filters["custom_filter"] = my_filter_func
```

## 依赖要求

需要安装 Jinja2：

```bash
pip install jinja2
```

Kuí 在导入时检查 Jinja2 是否可用，如果未找到则禁用模板支持。
