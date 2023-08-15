class ActionStorage:
    def __init__(self, _actions: dict[str, str] | None = None) -> None:
        if _actions is None:
            self.actions = dict()
        else:
            self.actions = dict(_actions)

    def __len__(self) -> int:
        return len(self.actions)

    def get_action(self, action_id: str) -> str:
        return self.actions[action_id]

    def retrieve_action(self, thought: str) -> str | None:
        """Simulated retrieval based on thought. You can implement a more detailed retrieval method."""
        for action in self.actions:
            if thought in action:
                return action
        return None

    def add_action(self, action_id: str, action: str) -> None:
        self.actions[action_id] = action

    def remove_action(self, action_id: str) -> None:
        self.actions.pop(action_id)
