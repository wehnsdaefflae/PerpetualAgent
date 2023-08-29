from typing import Callable

from new_attempt.model.storages.vector_storage.element import CONTENT_ELEMENT


class Callbacks:
    def __init__(self,
                 upsert_elements: Callable[[list[CONTENT_ELEMENT]], None],
                 remove_elements: Callable[[list[CONTENT_ELEMENT]], None]) -> None:

        self._upsert_elements = upsert_elements
        self._remove_elements = remove_elements

    def upsert_elements(self, elements: list[CONTENT_ELEMENT]) -> None:
        self._upsert_elements(elements)

    def remove_elements(self, elements: list[CONTENT_ELEMENT]) -> None:
        self._remove_elements(elements)
