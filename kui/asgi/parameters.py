from __future__ import annotations

import functools
import inspect
from contextlib import (
    _AsyncGeneratorContextManager,
    _GeneratorContextManager,
    asynccontextmanager,
    contextmanager,
)
from typing import Any, Callable, Dict, List, TypeVar
from typing import cast as typing_cast

from baize.datastructures import FormData
from pydantic import BaseModel, ValidationError

from ..exceptions import RequestValidationError
from ..parameters import (
    _convert_model_data_to_keyword_arguments,
    _create_new_signature,
    _merge_multi_value,
    _parse_depends_attrs,
    _parse_parameters_and_request_body_to_model,
    _update_docs,
    _validate_parameters,
    create_auto_params,
)
from ..utils import is_async_gen_callable, is_coroutine_callable, is_gen_callable
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
        security_info,
    ) = _parse_parameters_and_request_body_to_model(sig)

    depend_attrs = _parse_depends_attrs(sig)
    depend_functions = {
        name: _create_new_callback(info.call) for name, info in depend_attrs.items()
    }

    if not (parameters or request_body or depend_attrs):
        callback_with_auto_bound_params = callback
    else:

        @functools.wraps(callback)
        async def callback_with_auto_bound_params(*args, **kwargs) -> Any:
            data: List[BaseModel] = []
            keyword_params: Dict[str, Any] = {}

            need_closes: list[
                _GeneratorContextManager | _AsyncGeneratorContextManager
            ] = []
            try:
                # try to call depend functions
                cache = request.state.setdefault("depend_functions_cache", {})
                for name, function in depend_functions.items():
                    info = depend_attrs[name]
                    if info.cache and info.call in cache:
                        keyword_params[name] = cache[info.call]
                        continue
                    if is_async_gen_callable(info.call):
                        asyncgenerator = asynccontextmanager(function)()
                        if inspect.isawaitable(asyncgenerator.gen):
                            asyncgenerator.gen = await asyncgenerator.gen
                        keyword_params[name] = await asyncgenerator.__aenter__()
                        need_closes.append(asyncgenerator)
                    elif is_coroutine_callable(info.call):
                        keyword_params[name] = await function()
                    elif is_gen_callable(info.call):
                        generator = contextmanager(function)()
                        if inspect.isawaitable(generator.gen):
                            generator.gen = await generator.gen
                        keyword_params[name] = generator.__enter__()
                        need_closes.append(generator)
                    else:
                        result = function()
                        if inspect.isawaitable(result):
                            result = await result
                        keyword_params[name] = result

                    if info.cache:
                        cache[info.call] = keyword_params[name]

                # try to get parameters model and parse
                if parameters:
                    data.extend(_validate_parameters(parameters, request))

                # try to get body model and parse
                if request_body:
                    _body_data = await request.data()
                    if isinstance(_body_data, FormData):
                        _body_data = _merge_multi_value(_body_data.multi_items())

                    try:
                        data.append(
                            request_body.model_validate(_body_data)
                        )
                    except ValidationError as e:
                        raise RequestValidationError(e, "body")

                keyword_params.update(
                    _convert_model_data_to_keyword_arguments(data, exclusive_models)
                )

                result = callback(*args, **{**keyword_params, **kwargs})
                if inspect.isawaitable(result):
                    result = await result
                return result
            finally:
                for need_close in need_closes:
                    if isinstance(need_close, _GeneratorContextManager):
                        need_close.__exit__(None, None, None)
                    else:
                        await need_close.__aexit__(None, None, None)

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
        security_info,
    )

    return typing_cast(CallableObject, callback_with_auto_bound_params)


auto_params = create_auto_params(_create_new_callback)
