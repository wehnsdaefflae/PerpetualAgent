class FactStorage:
    def __init__(self) -> None:
        self._facts = []

    def retrieve_facts(self, thought: str) -> list[str]:
        """Simulated retrieval based on thought. You can implement a more detailed retrieval method."""
        for fact in self._facts:
            if thought in fact:
                return fact
        return [""]

    def add_fact(self, fact: str) -> None:
        self._facts.append(fact)
