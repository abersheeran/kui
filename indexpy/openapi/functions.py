import json
import typing
import functools
from inspect import signature

from starlette.requests import Request

from .models import Model


async def partial(
    handler: typing.Callable, request: Request
) -> typing.Optional[typing.Any]:

    sig = signature(handler)

    # try to get parameters model and parse
    query = sig.parameters.get("query")
    if query and issubclass(query.annotation, Model):
        _query = query.annotation(**request.query_params)
        handler = functools.partial(handler, query=_query)

    header = sig.parameters.get("header")
    if header and issubclass(header.annotation, Model):
        _header = header.annotation(**request.headers)
        handler = functools.partial(handler, header=_header)

    cookie = sig.parameters.get("cookie")
    if cookie and issubclass(cookie.annotation, Model):
        _cookie = cookie.annotation(**request.cookies)
        handler = functools.partial(handler, cookie=_cookie)

    # try to get body model and parse
    body = sig.parameters.get("body")
    if body and issubclass(body.annotation, Model):
        if request.headers.get("Content-Type") == "application/json":
            _body_data = await request.json()
        else:
            _body_data = await request.form()
        _body = body.annotation(**_body_data)
        handler = functools.partial(handler, body=_body)
    return handler


def describe(
    status: int, response_model: typing.Any = None, description: str = ""
) -> typing.Callable:
    """bind status => response model in http handler"""

    def decorator(func: typing.Callable) -> typing.Callable:
        """bind response model"""
        if hasattr(func, "__resps__"):
            getattr(func, "__resps__")[status] = {"model": response_model}
        else:
            setattr(func, "__resps__", {status: {"model": response_model}})

        getattr(func, "__resps__")[status]["description"] = description

        return func

    return decorator
