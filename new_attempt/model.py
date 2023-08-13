from new_attempt.storages.action_storage import ActionStorage
from new_attempt.storages.agent_storage import AgentStorage
from new_attempt.storages.fact_storage import FactStorage


class Model:
    def __init__(self):
        self._action_storage = ActionStorage()
        self.fact_storage = FactStorage()
        self._agent_storage = AgentStorage()
