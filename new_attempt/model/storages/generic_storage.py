from functools import lru_cache
from typing import TypeVar, Generic, Type

from chromadb.api.models.Collection import Collection
from chromadb.utils import embedding_functions

from new_attempt.logic.various import Fact, Action

ELEMENT = TypeVar("ELEMENT", Fact, Action)


class VectorStorage(Generic[ELEMENT]):
    def __init__(self, collection: Collection, clazz: Type[ELEMENT]) -> None:
        self.collection = collection
        self.embedding_function = embedding_functions.DefaultEmbeddingFunction()
        self.clazz = clazz

    def __len__(self) -> int:
        return self.collection.count()

    def _compose_id(self, fact_id: str, local_agent_id: str | None = None) -> str:
        return f"global:{fact_id}" if local_agent_id is None else f"local_{local_agent_id}:{fact_id}"

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
        documents = result["documents"][0]
        ids = result["ids"][0]
        return [self.clazz(each_doc, each_id, each_id.startswith("local:")) for each_doc, each_id in zip(documents, ids)]

    def add_element(self, document: str, local_agent_id: str | None = None) -> None:
        fact_id = f"global:{len(self)}" if local_agent_id is None else f"local_{local_agent_id}:{len(self)}"
        self.collection.add(
            ids=fact_id,
            metadatas=dict(),
            documents=document
        )

    def remove_element(self, ids: list[str], local_agent_id: str | None = None) -> None:
        full_ids = [self._compose_id(each_id, local_agent_id) for each_id in ids]
        self.collection.delete(ids=full_ids)
