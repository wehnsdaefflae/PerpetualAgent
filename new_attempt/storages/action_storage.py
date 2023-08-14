class ActionStorage:
    def __init__(self, _actions: dict[str, str] | None = None) -> None:
        if _actions is None:
            self._actions = dict()
        else:
            self._actions = dict(_actions)

    def retrieve_action(self, thought: str) -> str | None:
        """Simulated retrieval based on thought. You can implement a more detailed retrieval method."""
        for action in self._actions:
            if thought in action:
                return action
        return None

    def add_action(self, action_id: str, action: str) -> None:
        self._actions[action_id] = action

    def remove_action(self, action_id: str) -> None:
        self._actions.pop(action_id)
