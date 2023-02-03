from __future__ import annotations

import functools
import re
from typing import Any, Callable, Dict, Iterable, Pattern

from .requests import request
from .responses import convert_response
from .routing import SyncViewType


def allow_cors(
    allow_origins: Iterable[Pattern] = (re.compile(".*"),),
    allow_methods: Iterable[str] = (
        "GET",
        "POST",
        "PUT",
        "PATCH",
        "DELETE",
        "HEAD",
        "OPTIONS",
        "TRACE",
    ),
    allow_headers: Iterable[str] = (),
    expose_headers: Iterable[str] = (),
    allow_credentials: bool = False,
    max_age: int = 600,
) -> Callable[[SyncViewType], SyncViewType]:
    """
    Cross-Origin Resource Sharing
    """

    config_dict: Dict[str, str] = {
        "Access-Control-Allow-Methods": ", ".join(allow_methods),
        "Access-Control-Allow-Headers": ", ".join(
            {"Accept", "Accept-Language", "Content-Language", "Content-Type"}
            | set(allow_headers)
        ),
        "Access-Control-Expose-Headers": ", ".join(expose_headers),
        "Access-Control-Allow-Credentials": "true" if allow_credentials else "false",
        "Access-Control-Max-Age": str(max_age),
    }
    config_dict = {k: v for k, v in config_dict.items() if v}

    def decorator(endpoint: SyncViewType) -> SyncViewType:
        @functools.wraps(endpoint)
        def cors_wrapper() -> Any:
            origin = request.headers.get("origin", None)
            if origin and any(
                origin_pattern.fullmatch(origin) for origin_pattern in allow_origins
            ):
                response = convert_response(endpoint())
                response.headers.update(config_dict)
                response.headers["Access-Control-Allow-Origin"] = origin
                return response
            else:
                return endpoint()

        return cors_wrapper

    return decorator
