from __future__ import annotations

import functools
import inspect
from contextlib import AsyncExitStack, asynccontextmanager, contextmanager
from typing import Any, Callable, Dict, List, Tuple, Type, TypeVar
from typing import cast as typing_cast

from baize.datastructures import FormData
from pydantic import BaseModel

from ..parameters import (
    _convert_model_data_to_keyword_arguments,
    _create_new_signature,
    _merge_multi_value,
    _parse_depends_attrs,
    _parse_parameters_and_request_body_to_model,
    _update_docs,
    _validate_parameters_and_request_body,
    create_auto_params,
)
from ..parameters.fields import Depends
from ..utils import is_async_gen_callable, is_coroutine_callable, is_gen_callable
from .requests import http_connection, request

CallableObject = TypeVar("CallableObject", bound=Callable)


__all__ = [
    "auto_params",
]


async def call_dependencies_injection(
    depend_functions: Dict[str, Callable[..., Any]],
    depend_attrs: Dict[str, Depends],
    cache: Dict[Any, Any],
    close_soon: AsyncExitStack,
    after_response: AsyncExitStack,
) -> Dict[str, Any]:
    keyword_params: Dict[str, Any] = {}
    for name, function in depend_functions.items():
        info = depend_attrs[name]
        if info.cache and info.call in cache:
            keyword_params[name] = cache[info.call]
            continue
        if is_async_gen_callable(info.call):
            asyncgenerator = asynccontextmanager(function)()
            if inspect.isawaitable(asyncgenerator.gen):
                asyncgenerator.gen = await asyncgenerator.gen
            if info.cache:
                keyword_params[name] = await after_response.enter_async_context(
                    asyncgenerator
                )
            else:
                keyword_params[name] = await close_soon.enter_async_context(
                    asyncgenerator
                )
        elif is_coroutine_callable(info.call):
            keyword_params[name] = await function()
        elif is_gen_callable(info.call):
            generator = contextmanager(function)()
            if inspect.isawaitable(generator.gen):
                generator.gen = await generator.gen
            if info.cache:
                keyword_params[name] = after_response.enter_context(generator)
            else:
                keyword_params[name] = close_soon.enter_context(generator)
        else:
            result = function()
            if inspect.isawaitable(result):
                result = await result
            keyword_params[name] = result

        if info.cache:
            cache[info.call] = keyword_params[name]
    return keyword_params


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
        callback_with_auto_bound_params = callback  # type: ignore
    else:

        @functools.wraps(callback)
        async def callback_with_auto_bound_params(*args, **kwargs) -> Any:
            keyword_params: Dict[str, Any] = {}

            after_response = http_connection.exit_stack
            async with AsyncExitStack() as close_soon:
                # try to call depend functions
                cache = http_connection.state.setdefault("depend_functions_cache", {})
                depends_result = await call_dependencies_injection(
                    depend_functions,
                    depend_attrs,
                    cache,
                    close_soon=close_soon,
                    after_response=after_response,
                )
                keyword_params.update(depends_result)

                data: List[Tuple[Type[BaseModel], Any]]

                try:
                    g = _validate_parameters_and_request_body(
                        parameters or {}, request_body, http_connection
                    )
                    g.send(None)
                    _body_data = await request.data()
                    if isinstance(_body_data, FormData):
                        _body_data = _merge_multi_value(_body_data.multi_items())
                    g.send(_body_data)
                except StopIteration as e:
                    data = e.value
                else:
                    raise NotImplementedError

                keyword_params.update(
                    _convert_model_data_to_keyword_arguments(data, exclusive_models)
                )

                result = callback(*args, **{**keyword_params, **kwargs})
                if inspect.isawaitable(result):
                    result = await result
                return result

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
