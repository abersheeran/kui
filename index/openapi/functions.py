import json
import typing
from inspect import signature
from functools import wraps

from starlette.requests import Request

from .models import _OutputModel, QueryModel, FormModel
from .utils import currying


class ParseError(Exception):
    def __init__(self, error: typing.Any) -> None:
        self.error = error


async def partial(
    handler: typing.Callable, request: Request
) -> typing.Optional[typing.Any]:
    handler = currying(handler)
    sig = signature(handler)
    query = sig.parameters.get("query")
    if query and issubclass(query.annotation, QueryModel):
        _query = query.annotation(request.query_params)
        query_error = await _query.clean()
        if query_error:
            raise ParseError({"query": query_error})
        handler = handler(query=_query)

    body = sig.parameters.get("body")
    if body and issubclass(body.annotation, FormModel):
        if body.annotation.get_content_type() == "application/json":
            try:
                _body_data = await request.json()
            except json.decoder.JSONDecodeError:
                raise ParseError(
                    {"error": {"body": "You must submit a valid JSON string."}}
                )
        else:
            _body_data = await request.form()
        _body = body.annotation(_body_data)
        body_error = await _body.clean()
        if body_error:
            raise ParseError({"error": {"body": body_error}})
        handler = handler(body=_body)
    return handler


def bindresponse(
    status: int, response_model: _OutputModel, description: str = ""
) -> typing.Callable:
    """bind status => response model in http handler"""

    def decorator(func: typing.Callable) -> typing.Callable:
        """bind response model"""
        if hasattr(func, "__resps__"):
            getattr(func, "__resps__")[status] = {"model": response_model}
        else:
            setattr(func, "__resps__", {status: {"model": response_model}})

        getattr(func, "__resps__")[status]["description"] = description

        @wraps(func)
        def wrapper(*args, **kwargs):
            return func(*args, **kwargs)

        return wrapper

    return decorator
