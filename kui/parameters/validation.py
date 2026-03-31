from __future__ import annotations

from typing import (
    TYPE_CHECKING,
    Any,
    Dict,
    Generator,
    List,
    Sequence,
    Tuple,
    Type,
    Union,
)

from baize.datastructures import FormData
from pydantic import BaseModel, ValidationError
from typing_extensions import Literal

from ..exceptions import RequestValidationError
from ..pydantic_compatible import validate_model
from .parsing import sorted_groupby

if TYPE_CHECKING:
    from ..asgi.requests import HTTPConnection as ASGIConnection
    from ..wsgi.requests import HTTPConnection as WSGIConnection


def _merge_multi_value(
    items: Sequence[Tuple[str, Any]],
) -> Dict[str, Union[Any, List[Any]]]:
    """
    If there are values with the same key value, they are merged into a List.
    """
    return {
        k: v_list if len(v_list) > 1 else v_list[0]
        for k, v_list in (
            (k, [v for _, v in kv_iter])
            for k, kv_iter in sorted_groupby(items, lambda kv: kv[0])
        )
    }


def _validate_parameters_and_request_body(
    parameters: Dict[Literal["path", "query", "header", "cookie"], Type[BaseModel]],
    request_body: Type[BaseModel] | None,
    request: ASGIConnection | WSGIConnection,
) -> Generator[None, Any, List[Tuple[Type[BaseModel], Any]]]:
    # This generator uses a two-step protocol: callers `send(None)` to start it,
    # then `send(body_data)` to provide body data. The final value is returned
    # through `StopIteration.value`.
    data = []

    if "path" in parameters:
        try:
            data.append(validate_model(parameters["path"], request.path_params))
        except ValidationError as e:
            raise RequestValidationError(e, "path")

    if "query" in parameters:
        try:
            data.append(
                validate_model(
                    parameters["query"],
                    _merge_multi_value(request.query_params.multi_items()),
                )
            )
        except ValidationError as e:
            raise RequestValidationError(e, "query")

    if "header" in parameters:
        try:
            data.append(validate_model(parameters["header"], request.headers._dict))
        except ValidationError as e:
            raise RequestValidationError(e, "header")

    if "cookie" in parameters:
        try:
            data.append(validate_model(parameters["cookie"], request.cookies))
        except ValidationError as e:
            raise RequestValidationError(e, "cookie")

    # try to get body model and parse
    if request_body:
        _body_data = yield
        if isinstance(_body_data, FormData):
            _body_data = _merge_multi_value(_body_data.multi_items())

        try:
            data.append(validate_model(request_body, _body_data))
        except ValidationError as e:
            raise RequestValidationError(e, "body")

    return data


def _convert_model_data_to_keyword_arguments(
    data: List[Tuple[Type[BaseModel], Any]],
    exclusive_models: Dict[Type[BaseModel], str],
) -> Dict[str, Any]:
    result = {}
    for model, value in data:
        # `temporary_model` means a field-by-field parameter group whose fields
        # become kwargs directly; every other model is exclusive and maps back
        # to its original single parameter name.
        if model.__name__ == "temporary_model":
            result.update(value)
        else:
            result[exclusive_models[model]] = value
    return result
