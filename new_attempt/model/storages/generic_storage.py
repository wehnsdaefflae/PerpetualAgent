from abc import ABC, abstractmethod
from functools import lru_cache
from typing import TypeVar, Generic, Type

from chromadb.api.models.Collection import Collection
from chromadb.utils import embedding_functions


class __ContentElementForwardRef(ABC):
    pass


ELEMENT = TypeVar("ELEMENT", bound=__ContentElementForwardRef)


class ContentElement(__ContentElementForwardRef):
    @staticmethod
    @abstractmethod
    def from_dict(element_dict: dict[str, any]) -> ELEMENT:
        raise NotImplementedError()

    def __init__(self, content: str, **kwargs: any) -> None:
        self.content = content
        self._kwargs = kwargs
        self.storage_id = None

    def __hash__(self) -> int:
        return hash(self.storage_id)

    def to_dict(self) -> dict[str, any]:
        return {
            "content": self.content,
            "kwargs": self._kwargs,
            "storage_id": self.storage_id,
        }


class VectorStorage(Generic[ELEMENT]):
    @staticmethod
    def _compose_id(element_id: str, local_agent_id: str | None = None) -> str:
        return f"global:{element_id}" if local_agent_id is None else f"local_{local_agent_id}:{element_id}"

    @staticmethod
    @lru_cache(maxsize=128)
    def _embed(documents: list[str]) -> list[tuple[float, ...]]:
        # check: https://huggingface.co/spaces/mteb/leaderboard
        embedding_function = embedding_functions.DefaultEmbeddingFunction()

        vectors = embedding_function(documents)
        return [
            tuple(float(x) if not isinstance(x, float) else x for x in each_vector)
            for each_vector in vectors
        ]

    def __init__(self, collection: Collection, clazz: Type[ELEMENT]) -> None:
        self.collection = collection
        self.clazz = clazz

    def __len__(self) -> int:
        return self.collection.count()

    def _increment_storage_id(self) -> None:
        self.collection.metadata["next_storage_id"] = self._get_storage_id() + 1

    def _get_storage_id(self, incr: bool = False) -> int:
        storage_id = self.collection.metadata.get("next_storage_id", 0)
        if incr:
            self._increment_storage_id()
        return storage_id

    def store_contents(self, contents: list[str], local_agent_id: str | None = None) -> list[ELEMENT]:
        ids = list()
        metadatas = list()
        documents = list()

        elements = list()
        for each_content in contents:
            each_element = self.clazz(each_content)
            elements.append(each_element)

            raw_storage_id = str(self._get_storage_id(incr=True))
            storage_id = self._compose_id(raw_storage_id, local_agent_id=local_agent_id)
            each_element.storage_id = storage_id

            ids.append(storage_id)
            metadatas.append(each_element._kwargs)
            documents.append(each_content)

        embeddings = VectorStorage._embed(documents)

        self.collection.add(
            ids=ids,
            metadatas=metadatas,
            documents=documents,
            embeddings=embeddings
        )

        return elements

    def update_elements(self, elements: list[ELEMENT]) -> None:
        ids = [each_element.storage_id for each_element in elements]
        results = self.collection.get(ids=ids, include=["embeddings", "metadatas", "documents"])
        old_embeddings = dict(zip(results["ids"], results["embeddings"]))
        old_metadatas = dict(zip(results["ids"], results["metadatas"]))
        old_documents = dict(zip(results["ids"], results["documents"]))

        ids_changed_document = {
            each_element.storage_id
            for each_element in elements
            if each_element.content != old_documents[each_element.storage_id]
        }

        changed_contents = [each_element.content for each_element in elements if each_element.storage_id in ids_changed_document]
        updated_embeddings = dict(zip(ids_changed_document, VectorStorage._embed(changed_contents)))
        updated_metadata = {each_element.storage_id: each_element.kwargs for each_element in elements if each_element.kwargs != old_metadatas[each_element.storage_id]}

        new_ids = list()
        new_metadatas = list()
        new_documents = list()
        new_embeddings = list()

        for each_element in elements:
            each_id = each_element.storage_id
            if each_id not in updated_embeddings and each_id not in updated_metadata:
                continue

            each_metadata = updated_metadata.get(each_id, old_metadatas[each_id])
            each_embedding = updated_embeddings.get(each_id, old_embeddings[each_id])

            new_ids.append(each_id)
            new_metadatas.append(each_metadata)
            new_documents.append(each_element.content)
            new_embeddings.append(each_embedding)

        self.collection.update(
            ids=new_ids,
            embeddings=new_embeddings,
            metadatas=new_metadatas,
            documents=new_documents
        )

    def remove_elements(self, ids: list[str]) -> None:
        self.collection.delete(ids=ids)

    def get_elements(self, ids: list[str] | None = None, local_agent_id: str | None = None) -> list[ELEMENT]:
        result = self.collection.get(ids=ids)

        documents = result["documents"]
        ids = result["ids"]
        metadatas = result["metadatas"]

        elements = list()

        for each_doc, each_id, each_metadata in zip(documents, ids, metadatas):
            if local_agent_id is not None and not each_id.startswith(f"local_{local_agent_id}:"):
                continue
            each_element = self.clazz(each_doc, **each_metadata)
            each_element.storage_id = each_id
            elements.append(each_element)

        return elements

    def retrieve_elements(self, thought: str, n: int = 5) -> list[ELEMENT]:
        embedding, = self._embed([thought])
        result = self.collection.query(embedding, n_results=n)
        metadatas = result["metadatas"][0]
        documents = result["documents"][0]
        ids = result["ids"][0]

        elements = list()
        for each_doc, each_id, each_meta in zip(documents, ids, metadatas):
            each_element = self.clazz(each_doc, **each_meta)
            each_element.storage_id = each_id
            elements.append(each_element)

        return elements

