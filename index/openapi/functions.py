import json
import typing
import functools
from inspect import signature

from starlette.requests import Request

from .models import Model


class ParseError(Exception):
    def __init__(self, error: typing.Any) -> None:
        self.error = error


async def partial(
    handler: typing.Callable, request: Request
) -> typing.Optional[typing.Any]:

    sig = signature(handler)

    # try to get query model and parse
    query = sig.parameters.get("query")
    if query and issubclass(query.annotation, Model):
        _query = query.annotation(**request.query_params)
        handler = functools.partial(handler, query=_query)

    # try to get body model and parse
    body = sig.parameters.get("body")
    if body and issubclass(body.annotation, Model):
        try:
            _body_data = await request.json()
        except json.decoder.JSONDecodeError:
            _body_data = await request.form()
        _body = body.annotation(**_body_data)
        handler = functools.partial(handler, body=_body)
    return handler


def describe(
    status: int, response_model: Model = None, description: str = ""
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


class SchemaFromModel:
    @staticmethod
    def parameters(model: Model, position: str) -> typing.Dict[str, typing.Any]:
        """
        create openapi parameters docs from model.

        enum: "path", "query", "header", "cookie"

        https://swagger.io/docs/specification/describing-parameters/
        """
        assert position in ("path", "query", "header", "cookie")

        result = []
        for name, field in model.fields.items():
            schema = field.openapi()
            description = schema.pop("description")
            result.append(
                {
                    "in": position,
                    "name": name,
                    "schema": schema,
                    "description": description,
                    "required": not field.allow_null,
                }
            )
        return result

    @classmethod
    def in_path(cls, model: Model) -> typing.Dict[str, typing.Any]:
        return cls.parameters(model, "path")

    @classmethod
    def in_query(cls, model: Model) -> typing.Dict[str, typing.Any]:
        return cls.parameters(model, "query")

    @classmethod
    def in_header(cls, model: Model) -> typing.Dict[str, typing.Any]:
        return cls.parameters(model, "header")

    @classmethod
    def in_cookie(cls, model: Model) -> typing.Dict[str, typing.Any]:
        return cls.parameters(model, "cookie")
