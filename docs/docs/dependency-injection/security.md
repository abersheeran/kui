Kuí 提供了一系列依赖注入函数用于更方便的编写 API 鉴权，并会使用它们自动生成对应的 OpenAPI 文档。

## ApiKey

ApiKey 依赖注入函数接受两个参数。`name` 为 API Key 的名称，`position` 为 API Key 的位置，可选值为 `query`、`header`、`cookie`。

```python
api_key_auth_dependency(
    name: str,
    position: Literal["query", "header", "cookie"] = "header",
) -> Callable[[Union[str, None]], str]
```

如下例所示，我们可以通过 `api_key_auth_dependency` 函数创建一个依赖注入函数，用于从请求头中的 `api-key` 字段获取 API Key。

```python
def need_auth(
    api_key: Annotated[str, Depends(api_key_auth_dependency("api-key"))],
) -> str:
    return api_key
```

## HTTP Basic

通过 `basic_auth` 函数创建的依赖注入函数，会从请求头中的 `Authorization` 字段获取用户名和密码。你无需自行处理用户名和密码的解析，用户名和密码会作为一个元组返回。

```python
def need_auth(
    user_and_password: Annotated[Tuple[str, str], Depends(basic_auth)],
) -> str:
    return ", ".join(user_and_password)
```

## HTTP Bearer

通过 `bearer_auth` 函数创建的依赖注入函数，会从请求头中的 `Authorization` 字段获取不含 `Bearer` 前缀的 Token。

```python
def need_auth(
    token: Annotated[str, Depends(bearer_auth)],
) -> str:
    return token
```
