
class FactStorage:
    def __init__(self, _facts: dict[str, str] | None = None) -> None:
        if _facts is None:
            self._facts = dict()
        else:
            self._facts = dict(_facts)

    def get_fact(self, fact_id: str) -> str:
        return self._facts[fact_id]

    def retrieve_facts(self, thought: str) -> list[str]:
        """Simulated retrieval based on thought. You can implement a more detailed retrieval method."""
        facts = list()
        for fact in self._facts:
            if thought in fact:
                facts.append(fact)
        return facts

    def add_fact(self, fact: str) -> None:
        fact_id = f"{len(self._facts)}"
        self._facts[fact_id] = fact
