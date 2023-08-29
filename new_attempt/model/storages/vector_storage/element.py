from abc import ABC, abstractmethod
from typing import TypeVar


class __ContentElementForwardRef(ABC):
    pass


CONTENT_ELEMENT = TypeVar("CONTENT_ELEMENT", bound=__ContentElementForwardRef)


class ContentElement(__ContentElementForwardRef):
    @staticmethod
    @abstractmethod
    def from_dict(element_dict: dict[str, any]) -> CONTENT_ELEMENT:
        raise NotImplementedError()

    def __init__(self, content: str, **kwargs: any) -> None:
        self.content = content
        self.kwargs = kwargs
        self.storage_id = None

    def __hash__(self) -> int:
        return hash(self.storage_id)

    def to_dict(self) -> dict[str, any]:
        return {
            "content": self.content,
            "kwargs": self.kwargs,
            "storage_id": self.storage_id,
        }
