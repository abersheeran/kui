from __future__ import annotations

from typing import Any, Dict, Generic, NoReturn, Tuple, TypeVar, overload

T = TypeVar("T")


class Singleton(type):
    def __init__(
        cls,
        name: str,
        bases: Tuple[type],
        namespace: Dict[str, Any],
    ) -> None:
        cls.instance = None
        super().__init__(name, bases, namespace)

    def __call__(cls, *args, **kwargs) -> Any:
        if cls.instance is None:
            cls.instance = super().__call__(*args, **kwargs)
        return cls.instance


class ImmutableAttribute(Generic[T]):
    def __set_name__(self, owner: object, name: str) -> None:
        self.public_name = name
        self.private_name = "_" + name

    @overload
    def __get__(self, instance: None, cls: type | None) -> NoReturn:
        ...

    @overload
    def __get__(self, instance: object, cls: type | None) -> T:
        ...

    def __get__(self, instance, cls):
        if instance is None:
            raise AttributeError(
                f"{instance.__class__.__name__} has no attribute '{self.public_name}'"
            ) from None
        else:
            return getattr(instance, self.private_name)

    def __set__(self, instance: object, value: T) -> None:
        if hasattr(instance, self.private_name):
            raise RuntimeError(
                f"{instance.__class__.__name__}.{self.public_name} is immutable"
            ) from None
        setattr(instance, self.private_name, value)

    def __delete__(self, instance: object) -> None:
        raise RuntimeError(
            f"{instance.__class__.__name__}.{self.public_name} is immutable"
        ) from None
