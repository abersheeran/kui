from typing import Iterable, Pattern

from typing_extensions import TypedDict


class CORSConfig(TypedDict, total=False):
    allow_origins: Iterable[Pattern]
    allow_methods: Iterable[str]
    allow_headers: Iterable[str]
    expose_headers: Iterable[str]
    allow_credentials: bool
    max_age: int
