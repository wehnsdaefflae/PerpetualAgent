from functools import lru_cache
from typing import TypeVar, Generic, Type

from chromadb.api.models.Collection import Collection
from chromadb.utils import embedding_functions

from new_attempt.logic.various import Fact, Action


class ContentElement:
    def __init__(self, element_id: str, content: str, **kwargs: any) -> None:
        # todo: use this
        self.content = content
        self.element_id = element_id
        self.kwargs = kwargs


ELEMENT = TypeVar("ELEMENT", bound=ContentElement)


class VectorStorage(Generic[ELEMENT]):
    def __init__(self, collection: Collection, clazz: Type[ELEMENT]) -> None:
        self.collection = collection
        self.embedding_function = embedding_functions.DefaultEmbeddingFunction()
        self.clazz = clazz
        self.element_count = 0

    def __len__(self) -> int:
        return self.collection.count()

    def _next_id(self) -> int:
        return self.element_count + 1

    def _compose_id(self, element_id: str, local_agent_id: str | None = None) -> str:
        return f"global:{element_id}" if local_agent_id is None else f"local_{local_agent_id}:{element_id}"

    def get_elements(self, ids: list[str] | None = None, local_agent_id: str | None = None) -> list[ELEMENT]:
        result = self.collection.get(ids=ids)
        documents = result["documents"]
        ids = result["ids"]
        if local_agent_id is None:
            return [
                self.clazz(each_doc, each_id)
                for each_doc, each_id in zip(documents, ids)
            ]
        return [
            self.clazz(each_doc, each_id)
            for each_doc, each_id in zip(documents, ids)
            if each_id.startswith(f"local_{local_agent_id}:")
        ]

    @lru_cache(maxsize=128)
    def _embed(self, documents: list[str]) -> tuple[tuple[float, ...], ...]:
        # check: https://huggingface.co/spaces/mteb/leaderboard
        vectors = self.embedding_function(documents)
        return tuple(
            tuple(float(x) if not isinstance(x, float) else x for x in each_vector)
            for each_vector in vectors
        )

    def retrieve_elements(self, thought: str, n: int = 5) -> list[ELEMENT]:
        embedding, = self._embed([thought])
        result = self.collection.query(embedding, n_results=n)
        metadatas = result["metadatas"][0]
        documents = result["documents"][0]
        ids = result["ids"][0]
        return [self.clazz(each_doc, each_id, **each_meta) for each_doc, each_id, each_meta in zip(documents, ids, metadatas)]

    def add_content(self, document: str, metadata: dict[str, any] | None = None, local_agent_id: str | None = None) -> ELEMENT:
        element_id = self._compose_id(str(self._next_id()), local_agent_id=local_agent_id)
        metadata = metadata or dict()
        self.collection.add(
            ids=element_id,
            metadatas=metadata,
            documents=document
        )
        self.element_count += 1
        return self.clazz(document, element_id, **metadata)

    def update_element(self, element: ELEMENT) -> None:
        if isinstance(element, Fact):
            metadatas = {"last_access": element.last_access}
            document = element.fact

        elif isinstance(element, Action):
            metadatas = {"success": element.success, "failure": element.failure}
            document = element.action

        else:
            raise TypeError(f"Undefined element type {type(element)}.")

        embedding, = self.embedding_function([document])

        self.collection.upsert(
            ids=element.element_id,
            embeddings=embedding,
            metadatas=metadatas,
            documents=element.action
        )

    def remove_element(self, ids: list[str], local_agent_id: str | None = None) -> None:
        full_ids = [self._compose_id(each_id, local_agent_id) for each_id in ids]
        self.collection.delete(ids=full_ids)
