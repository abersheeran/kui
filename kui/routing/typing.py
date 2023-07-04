import typing

SyncView = typing.Callable[..., typing.Any]
AsyncView = typing.Callable[..., typing.Awaitable[typing.Any]]


SyncViewType = typing.TypeVar("SyncViewType", bound=SyncView)
AsyncViewType = typing.TypeVar("AsyncViewType", bound=AsyncView)
ViewType = typing.TypeVar("ViewType", bound=typing.Union[SyncView, AsyncView])
MiddlewareType = typing.Callable[[ViewType], ViewType]
