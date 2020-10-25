import functools
import typing
from http import HTTPStatus
from inspect import isclass, signature

from pydantic import BaseModel, ValidationError

from indexpy.http import Request

T = typing.TypeVar("T", bound=typing.Callable)


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

    https://github.com/OAI/OpenAPI-Specification/blob/master/versions/3.0.0.md#responseObject
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


def merge_openapi_info(
    operation_info: typing.Dict[str, typing.Any],
    more_info: typing.Dict[str, typing.Any],
) -> typing.Dict[str, typing.Any]:
    for key, value in more_info.items():
        if key in operation_info:
            if isinstance(operation_info[key], typing.Sequence):
                operation_info[key] = _ = list(operation_info[key])
                _.extend(value)
                continue
            elif isinstance(operation_info[key], dict):
                operation_info[key] = merge_openapi_info(operation_info[key], value)
                continue
        operation_info[key] = value
    return operation_info


def describe_extra_docs(handler: T, info: typing.Dict[str, typing.Any]) -> T:
    """
    describe more openapi info in HTTP handler

    https://github.com/OAI/OpenAPI-Specification/blob/master/versions/3.0.0.md#operationObject
    """
    if isclass(handler):
        for method in getattr(handler, "__methods__"):
            setattr(getattr(handler, method.lower()), "__extra_docs__", info)
    else:
        setattr(handler, "__extra_docs__", info)
    return handler


def parse_params(function: T) -> T:
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

    params = {
        param_name: sig.parameters[param_name].annotation
        for param_name in param_names
        if (
            param_name in sig.parameters
            and issubclass(sig.parameters[param_name].annotation, BaseModel)
        )
    }
    if "body" in params:
        setattr(function, "__request_body__", params.pop("body"))
    if params:
        setattr(function, "__parameters__", params)
    return function


def _merge_multi_value(raw_list):
    """
    If there are values with the same key value, they are merged into a List.
    """
    d = {}
    for k, v in raw_list:
        if k not in d:
            d[k] = v
            continue
        if isinstance(d[k], list):
            d[k].append(v)
        else:
            d[k] = [d[k], v]
    return d


class ParamsValidationError(Exception):
    def __init__(self, validation_error: ValidationError) -> None:
        self.ve = validation_error


async def bound_params(handler: typing.Callable, request: Request) -> typing.Callable:
    """
    bound parameters "path", "query", "header", "cookie", "body" to the view function
    """
    parameters = getattr(handler, "__parameters__", None)
    request_body = getattr(handler, "__request_body__", None)
    if not (parameters or request_body):
        return handler

    kwargs: typing.Dict[str, BaseModel] = {}

    try:
        # try to get parameters model and parse
        if "path" in parameters:
            kwargs["path"] = parameters["path"](**request.path_params)

        if "query" in parameters:
            kwargs["query"] = parameters["query"](
                **_merge_multi_value(request.query_params.multi_items())
            )

        if "header" in parameters:
            kwargs["header"] = parameters["header"](
                **_merge_multi_value(request.headers.items())
            )

        if "cookie" in parameters:
            kwargs["cookie"] = parameters["cookie"](**request.cookies)

        # try to get body model and parse
        if request_body:
            if request.headers.get("Content-Type") == "application/json":
                _body_data = await request.json()
            else:
                _body_data = await request.form()
            kwargs["body"] = request_body(**_body_data)

    except ValidationError as e:
        raise ParamsValidationError(e)

    return functools.partial(handler, **kwargs)
