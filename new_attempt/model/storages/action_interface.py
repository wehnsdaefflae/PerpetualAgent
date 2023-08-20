from functools import lru_cache

from chromadb.api.models.Collection import Collection
from chromadb.utils import embedding_functions


class ActionInterface:
    def __init__(self, collection: Collection) -> None:
        self.collection = collection
        self.embedding_function = embedding_functions.DefaultEmbeddingFunction()

    def __len__(self) -> int:
        return self.collection.count()

    def get_action(self, action_id: str) -> str:
        result = self.collection.get(action_id)
        documents = result["documents"]
        return documents[0]

    @lru_cache(maxsize=128)
    def embed(self, actions: list[str]) -> tuple[tuple[float, ...], ...]:
        vectors = self.embedding_function(actions)
        return tuple(
            tuple(float(x) if not isinstance(x, float) else x for x in each_vector)
            for each_vector in vectors
        )

    def retrieve_action(self, thought: str, n: int = 1) -> tuple[str, float]:
        embedding, = self.embed([thought])
        result = self.collection.query(embedding, n_results=n)
        documents, = result["documents"]
        distances, = result["distances"]
        return documents[0], distances[0]

    def add_action(self, action: str) -> None:
        action_id = f"{len(self)}"
        self.collection.add(
            ids=action_id,
            metadatas=dict(),
            documents=action
        )

    def remove_action(self, action_id: str) -> None:
        self.collection.delete(ids=[action_id])
