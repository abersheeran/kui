Kuí provides a series of dependency injection functions for easier API authentication and automatically generates corresponding OpenAPI documentation for them.

## ApiKey

The `ApiKey` dependency injection function accepts two parameters. The `name` is the name of the API Key, and the `position` is the position of the API Key, which can be either `query`, `header`, or `cookie`.

```python
api_key_auth_dependency(
    name: str,
    position: Literal["query", "header", "cookie"] = "header",
) -> Callable[[Union[str, None]], str]
```

As shown in the following example, we can create a dependency injection function using the `api_key_auth_dependency` function to retrieve the API Key from the `api-key` field in the request header.

```python
def need_auth(
    api_key: Annotated[str, Depends(api_key_auth_dependency("api-key"))],
) -> str:
    return api_key
```

## HTTP Basic

The dependency injection function created using the `basic_auth` function retrieves the username and password from the `Authorization` field in the request header. You don't need to handle the parsing of the username and password yourself; they will be returned as a tuple.

```python
def need_auth(
    user_and_password: Annotated[Tuple[str, str], Depends(basic_auth)],
) -> str:
    return ", ".join(user_and_password)
```

## HTTP Bearer

The dependency injection function created using the `bearer_auth` function retrieves the Token without the `Bearer` prefix from the `Authorization` field in the request header.

```python
def need_auth(
    token: Annotated[str, Depends(bearer_auth)],
) -> str:
    return token
```
