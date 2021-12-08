import functools
import re
import typing
from typing import Any, Callable, Dict, Iterable, Pattern, TypeVar

from .. import request
from ..responses import convert_response

_View = TypeVar("_View", bound=Callable)


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
) -> Callable[[_View], _View]:
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

    def decorator(endpoint: _View) -> _View:
        @functools.wraps(endpoint)
        def cors_wrapper(*args: Any, **kwargs: Any) -> Any:
            origin = request.headers.get("origin", None)
            if origin and any(
                origin_pattern.fullmatch(origin) for origin_pattern in allow_origins
            ):
                response = convert_response(endpoint(*args, **kwargs))
                response.headers.update(config_dict)
                response.headers["Access-Control-Allow-Origin"] = origin
                return response
            else:
                return endpoint(*args, **kwargs)

        return typing.cast(_View, cors_wrapper)

    return decorator


CORSMiddleware = allow_cors
