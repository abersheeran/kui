from __future__ import annotations

import functools
import inspect
from contextlib import contextmanager
from typing import Any, Callable, Dict, List, TypeVar

from baize.datastructures import FormData
from pydantic import BaseModel, ValidationError

from ..exceptions import RequestValidationError
from ..parameters import (
    _convert_model_data_to_keyword_arguments,
    _create_new_signature,
    _merge_multi_value,
    _parse_depends_attrs,
    _parse_parameters_and_request_body_to_model,
    _parse_request_attrs,
    _update_docs,
    _validate_parameters,
    _validate_request_attr,
    create_auto_params,
)
from ..utils import is_gen_callable
from .requests import request

CallableObject = TypeVar("CallableObject", bound=Callable)


__all__ = [
    "auto_params",
]


def _create_new_callback(callback: CallableObject) -> CallableObject:
    sig = inspect.signature(callback)

    (
        parameters,
        request_body,
        exclusive_models,
    ) = _parse_parameters_and_request_body_to_model(sig)

    request_attrs = _parse_request_attrs(sig)

    depend_attrs = _parse_depends_attrs(sig)
    depend_functions = {
        name: _create_new_callback(info.call) for name, info in depend_attrs.items()
    }

    if not (parameters or request_body or request_attrs or depend_attrs):
        callback_with_auto_bound_params = callback
    else:

        @functools.wraps(callback)
        def callback_with_auto_bound_params(*args, **kwargs) -> Any:
            data: List[BaseModel] = []
            keyword_params: Dict[str, Any] = {}

            need_closes = []
            try:
                # try to call depend functions
                cache = request.state.setdefault("depend_functions_cache", {})
                for name, function in depend_functions.items():
                    info = depend_attrs[name]
                    if info.call in cache:
                        keyword_params[name] = cache[info.call]
                        continue
                    if is_gen_callable(info.call):
                        generator = contextmanager(function)()
                        keyword_params[name] = generator.__enter__()
                        need_closes.append(generator)
                    else:
                        result = function()
                        keyword_params[name] = result

                    if info.cache:
                        cache[info.call] = keyword_params[name]

                # try to get parameters model and parse
                if parameters:
                    data.extend(_validate_parameters(parameters, request))

                # try to get body model and parse
                if request_body:
                    _body_data = request.data()
                    if isinstance(_body_data, FormData):
                        _body_data = _merge_multi_value(_body_data.multi_items())

                    try:
                        data.append(request_body.parse_obj(_body_data))
                    except ValidationError as e:
                        raise RequestValidationError(e, "body")

                # try to get request instance attributes
                if request_attrs:
                    keyword_params.update(
                        _validate_request_attr(request_attrs, request)
                    )

                keyword_params.update(
                    _convert_model_data_to_keyword_arguments(data, exclusive_models)
                )

                result = callback(*args, **{**keyword_params, **kwargs})  # type: ignore
                return result
            finally:
                for need_close in need_closes:
                    need_close.__exit__(None, None, None)

        del callback_with_auto_bound_params.__wrapped__  # type: ignore

        setattr(
            callback_with_auto_bound_params, "__signature__", _create_new_signature(sig)
        )

    _update_docs(
        callback,
        callback_with_auto_bound_params,
        parameters,
        request_body,
        depend_functions,
    )

    return callback_with_auto_bound_params  # type: ignore


auto_params = create_auto_params(_create_new_callback)
