from abc import ABC, abstractmethod
from typing import TypeVar


class __DictableForwardRef(ABC):
    pass


D = TypeVar("D", bound=__DictableForwardRef)


class Dictable(__DictableForwardRef):
    @staticmethod
    @abstractmethod
    def from_dict(element_dict: dict[str, any]) -> D:
        raise NotImplementedError()

    @abstractmethod
    def to_dict(self) -> dict[str, any]:
        raise NotImplementedError()


def not_implemented(*args: any, **kwargs: any) -> any:
    raise NotImplementedError("must be set by controller")

