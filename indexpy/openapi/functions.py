from __future__ import annotations

import sys
import typing
from http import HTTPStatus
from inspect import isclass

from pydantic import BaseModel, create_model
from pydantic.typing import display_as_type

if sys.version_info >= (3, 9):
    from types import GenericAlias
    from typing import _SpecialGenericAlias, _GenericAlias

    GenericType = (GenericAlias, _SpecialGenericAlias, _GenericAlias)
else:
    from typing import _GenericAlias

    GenericType = (_GenericAlias,)


T = typing.TypeVar("T", bound=typing.Callable)


def describe_response(
    status: typing.Union[int, HTTPStatus],
    description: str = "",
    *,
    content: typing.Union[typing.Type[BaseModel], type, dict] = None,
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
            if isinstance(content, dict) or (
                not isinstance(content, GenericType)
                and isclass(content)
                and issubclass(content, BaseModel)
            ):
                responses[status]["content"] = content
            else:
                responses[status]["content"] = create_model(
                    f"ParsingModel[{display_as_type(content)}]", __root__=(content, ...)
                )
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
    __extra_docs__ = merge_openapi_info(getattr(handler, "__extra_docs__", {}), info)

    if isclass(handler):
        for method in getattr(handler, "__methods__"):
            setattr(getattr(handler, method.lower()), "__extra_docs__", __extra_docs__)
    else:
        setattr(handler, "__extra_docs__", __extra_docs__)
    return handler
