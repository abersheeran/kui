from __future__ import annotations

import typing

from ..routing import ViewType


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


def describe_extra_docs(
    handler: ViewType, info: typing.Dict[str, typing.Any]
) -> ViewType:
    """
    describe more openapi info in HTTP handler

    https://github.com/OAI/OpenAPI-Specification/blob/master/versions/3.0.3.md#operationObject
    """
    if isinstance(handler, type):
        for method in getattr(handler, "__methods__"):
            handler_method = getattr(handler, method.lower())
            __extra_docs__ = merge_openapi_info(
                getattr(handler_method, "__docs_extra__", {}), info
            )
            setattr(handler_method, "__docs_extra__", __extra_docs__)
    else:
        __extra_docs__ = merge_openapi_info(
            getattr(handler, "__docs_extra__", {}), info
        )
        setattr(handler, "__docs_extra__", __extra_docs__)
    return typing.cast(ViewType, handler)
