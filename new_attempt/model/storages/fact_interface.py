from functools import lru_cache

from chromadb.api.models.Collection import Collection
from chromadb.utils import embedding_functions


class FactInterface:
    def __init__(self, collection: Collection) -> None:
        self.collection = collection
        self.embedding_function = embedding_functions.DefaultEmbeddingFunction()

    def __len__(self) -> int:
        return self.collection.count()

    def get_fact(self, fact_id: str) -> str:
        result = self.collection.get(fact_id)
        documents = result["documents"]
        return documents[0]

    @lru_cache(maxsize=128)
    def embed(self, facts: list[str]) -> tuple[tuple[float, ...], ...]:
        vectors = self.embedding_function(facts)
        return tuple(
            tuple(float(x) if not isinstance(x, float) else x for x in each_vector)
            for each_vector in vectors
        )

    def retrieve_facts(self, thought: str, n: int = 5) -> list[str]:
        embedding, = self.embed([thought])
        result = self.collection.query(embedding, n_results=n)
        documents = result["documents"]
        return documents[0]

    def add_fact(self, fact: str) -> None:
        fact_id = f"{len(self)}"
        self.collection.add(
            ids=fact_id,
            metadatas=dict(),
            documents=fact
        )

    def remove_fact(self, fact_id: str) -> None:
        self.collection.delete(ids=[fact_id])
