import operator
from typing import Callable, Dict, Iterator, MutableMapping, TypeVar

KT = TypeVar("KT")
VT = TypeVar("VT")


class RegisterDict(MutableMapping[KT, VT]):
    """
    A mapping that can be used to register items.
    """

    def __init__(self) -> None:
        self._store: Dict[KT, VT] = {}

    def __getitem__(self, key: KT) -> VT:
        return self._store[key]

    def __setitem__(self, key: KT, value: VT) -> None:
        self._store[key] = value

    def __delitem__(self, key: KT) -> None:
        del self._store[key]

    def __iter__(self) -> Iterator[KT]:
        return iter(self._store)

    def __len__(self) -> int:
        return len(self._store)

    def register(self, key: KT) -> Callable[[VT], VT]:
        return lambda value: operator.setitem(self, key, value) or value
