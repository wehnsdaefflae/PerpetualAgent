class ActionStorage:
    def __init__(self) -> None:
        self._actions = []

    def retrieve_action(self, thought: str) -> str:
        """Simulated retrieval based on thought. You can implement a more detailed retrieval method."""
        for action in self._actions:
            if thought in action:
                return action
        return ""

    def add_action(self, action: str) -> None:
        self._actions.append(action)

    def remove_action(self, action: str) -> None:
        self._actions.remove(action)
