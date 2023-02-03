import typing

SyncViewType = typing.Callable[..., typing.Any]
AsyncViewType = typing.Callable[..., typing.Awaitable[typing.Any]]

ViewType = typing.TypeVar("ViewType", bound=typing.Union[SyncViewType, AsyncViewType])
MiddlewareType = typing.Callable[[ViewType], ViewType]
