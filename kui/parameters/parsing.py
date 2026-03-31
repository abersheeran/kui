from __future__ import annotations

import inspect
from itertools import groupby
from typing import Any, Dict, Tuple, Type, Union
from typing import cast as typing_cast

from pydantic import BaseModel, create_model
from pydantic.fields import FieldInfo
from typing_extensions import Annotated, Literal, get_args, get_origin

from ..pydantic_compatible import create_root_model
from ..utils import safe_issubclass
from .fields import (
    BaseHTTPFieldInfo,
    Depends,
    InBody,
    InCookie,
    InHeader,
    InPath,
    InQuery,
)


def get_annotated_args(tp):
    # Recursively flatten nested Annotated types so callers can scan one linear metadata list.
    return [
        j
        for i in (
            (get_annotated_args(t) if get_origin(t) is Annotated else [t])  # type: ignore
            for t in get_args(tp)
        )
        for j in i
    ]


def sorted_groupby(iterable, key):
    # itertools.groupby only groups consecutive elements, so sort first to collect equal keys together.
    return groupby(sorted(iterable, key=key), key=key)


def _parse_parameters_and_request_body_to_model(
    sig: inspect.Signature,
) -> Tuple[
    Dict[Literal["path", "query", "header", "cookie"], Type[BaseModel]] | None,
    Type[BaseModel] | None,
    Dict[Type[BaseModel], str],
    Dict[Literal["path", "query", "header", "cookie"], Dict[str, Any]],
]:
    raw_parameters: Dict[str, Any] = {
        key: {} for key in ["path", "query", "header", "cookie", "body"]
    }
    exclusive_models: Dict[Type[BaseModel], str] = {}
    security_info: Dict[
        Literal["path", "query", "header", "cookie"], Dict[str, Any]
    ] = {"path": {}, "query": {}, "header": {}, "cookie": {}}

    for name, param in sig.parameters.items():
        if not (
            get_origin(param.default) is Annotated
            or get_origin(param.annotation) is Annotated
        ):
            continue

        if param.POSITIONAL_ONLY:
            raise TypeError(
                f"Parameter {name} cannot be defined as positional only parameters."
            )

        annontated_define = param.annotation
        if get_origin(param.default) is Annotated:
            annontated_define = Annotated[annontated_define, param.default]

        type_, *annontated_list = get_annotated_args(annontated_define)
        kui_field: Union[InPath, InQuery, InHeader, InCookie, InBody]
        for kui_field in filter(
            lambda x: isinstance(x, (InPath, InQuery, InHeader, InCookie, InBody)),
            annontated_list,
        ):
            break
        else:
            # If there is no kui field, skip it.
            continue

        if kui_field.exclusive:
            # In exclusive mode, the entire source maps to one parameter through a root model.
            model = create_root_model(type_)
            raw_parameters[kui_field._in] = model
            exclusive_models[model] = name
        else:
            if safe_issubclass(raw_parameters[kui_field._in], BaseModel):
                raise RuntimeError(
                    f"{kui_field._in.capitalize()}(exclusive=True) "
                    f"and {kui_field._in.capitalize()} cannot be used at the same time"
                )
            field_info = next(
                filter(lambda x: isinstance(x, FieldInfo), annontated_list)
            )
            raw_parameters[kui_field._in][name] = (type_, field_info)
            if (
                isinstance(kui_field, (InQuery, InHeader, InCookie))
                and kui_field.security
            ):
                security_info[kui_field._in][field_info.alias or name] = (
                    kui_field.security
                )

    for key, params in filter(
        lambda kv: kv[1],
        ((key, raw_parameters.pop(key)) for key in tuple(raw_parameters.keys())),
    ):
        if safe_issubclass(params, BaseModel):
            model = params
        else:
            model = create_model("temporary_model", **params)
        raw_parameters[key] = model

    request_body: Type[BaseModel] | None
    if "body" in raw_parameters:
        request_body = raw_parameters.pop("body")
    else:
        request_body = None

    parameters: Dict[str, Type[BaseModel]] | None
    if raw_parameters:
        parameters = typing_cast(Dict[str, Type[BaseModel]], raw_parameters)
    else:
        parameters = None

    return (
        typing_cast(
            Dict[Literal["path", "query", "header", "cookie"], Type[BaseModel]],
            parameters,
        ),
        request_body,
        exclusive_models,
        security_info,
    )


def _parse_depends_attrs(sig: inspect.Signature) -> Dict[str, Depends]:
    return {
        **{
            name: next(
                filter(lambda x: isinstance(x, Depends), get_args(param.annotation))
            )
            for name, param in sig.parameters.items()
            if (
                get_origin(param.annotation) is Annotated
                and any(isinstance(arg, Depends) for arg in get_args(param.annotation))
            )
        },
        **{
            name: param.default
            for name, param in sig.parameters.items()
            if isinstance(param.default, Depends)
        },
    }


def _create_new_signature(sig: inspect.Signature) -> inspect.Signature:
    return inspect.Signature(
        parameters=[
            param
            for param in sig.parameters.values()
            if not (
                isinstance(param.default, (BaseHTTPFieldInfo, Depends))
                or (
                    get_origin(param.annotation) is Annotated
                    and isinstance(get_args(param.annotation)[1], FieldInfo)
                )
            )
        ],
        return_annotation=sig.return_annotation,
    )
