import functools
import typing
from http import HTTPStatus
from inspect import isclass, signature

from pydantic import BaseModel, ValidationError

from indexpy.http import Request

T = typing.TypeVar("T")


def describe_response(
    status: typing.Union[int, HTTPStatus],
    description: str = "",
    *,
    content: typing.Union[typing.Type[BaseModel], dict] = None,
    headers: dict = None,
    links: dict = None,
) -> typing.Callable[[T], T]:
    """
    describe a response in HTTP view function

    https://github.com/OAI/OpenAPI-Specification/blob/master/versions/3.0.2.md#responseObject
    """
    status = int(status)
    if not description:
        description = HTTPStatus(status).description

    def decorator(func: T) -> T:
        if not hasattr(func, "__responses__"):
            responses: typing.Dict[int, typing.Dict[str, typing.Any]] = {}
            setattr(func, "__responses__", responses)
        else:
            responses = getattr(func, "__responses__")
        responses[status] = {"description": description}

        if content is not None:
            responses[status]["content"] = content
        if headers is not None:
            responses[status]["headers"] = headers
        if links is not None:
            responses[status]["links"] = links

        return func

    return decorator


def describe_responses(responses: typing.Dict[int, dict]) -> typing.Callable[[T], T]:
    """
    describe responses in HTTP view function
    """

    def decorator(func: T) -> T:
        for status, info in responses.items():
            func = describe_response(status, **info)(func)
        return func

    return decorator


class ParamsValidationError(Exception):
    def __init__(self, validation_error: ValidationError) -> None:
        self.ve = validation_error


def parse_params(function: typing.Callable) -> typing.Callable:
    """
    parse function params "path", "query", "header", "cookie", "body"
    """
    param_names = ("path", "query", "header", "cookie", "body")
    sig = signature(function)

    incorrect_keys = [
        param_name
        for param_name in param_names
        if (
            param_name in sig.parameters
            and not issubclass(sig.parameters[param_name].annotation, BaseModel)
        )
    ]
    if incorrect_keys:
        raise TypeError(
            f"Params {incorrect_keys} annotation is incorrect in `{function.__name__}`. "
            + "You should inherit `pydantic.BaseModel`."
        )

    __params__ = {
        param_name: sig.parameters[param_name].annotation
        for param_name in param_names
        if (
            param_name in sig.parameters
            and issubclass(sig.parameters[param_name].annotation, BaseModel)
        )
    }
    if __params__:
        setattr(function, "__params__", __params__)
    return function


def merge_list(
    raw: typing.List[typing.Tuple[str, str]]
) -> typing.Dict[str, typing.Union[typing.List[str], str]]:
    """
    If there are values with the same key value, they are merged into a List.
    """
    d: typing.Dict[str, typing.Union[typing.List[str], str]] = {}
    for k, v in raw:
        if k in d:
            if isinstance(d[k], list):
                typing.cast(typing.List, d[k]).append(v)
            else:
                d[k] = [typing.cast(str, d[k]), v]
        else:
            d[k] = v
    return d


async def bound_params(handler: typing.Callable, request: Request) -> typing.Callable:
    """
    bound parameters "path", "query", "header", "cookie", "body" to the view function
    """
    if isclass(handler):
        return handler

    __params__ = getattr(handler, "__params__", None)
    if not __params__:
        return handler

    params: typing.Dict[str, BaseModel] = {}

    try:
        # try to get parameters model and parse
        if "path" in __params__:
            params["path"] = __params__["path"](**request.path_params)

        if "query" in __params__:
            params["query"] = __params__["query"](
                **merge_list(request.query_params.multi_items())
            )

        if "header" in __params__:
            params["header"] = __params__["header"](
                **merge_list(request.headers.items())
            )

        if "cookie" in __params__:
            params["cookie"] = __params__["cookie"](**request.cookies)

        # try to get body model and parse
        if "body" in __params__:
            if request.headers.get("Content-Type") == "application/json":
                _body_data = await request.json()
            else:
                _body_data = await request.form()
            params["body"] = __params__["body"](**_body_data)

    except ValidationError as e:
        raise ParamsValidationError(e)

    return functools.partial(handler, **params)
