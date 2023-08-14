from typing import Callable

from new_attempt.agent import Agent, AgentArguments
from new_attempt.storages.action_storage import ActionStorage
from new_attempt.storages.agent_storage import AgentStorage
from new_attempt.storages.fact_storage import FactStorage


class Model:
    def __init__(self, trigger_new_agent: Callable[[Agent], None]) -> None:
        self.action_storage = ActionStorage()
        self.fact_storage = FactStorage()
        self.agent_storage = AgentStorage()

        self.trigger_new_agent = trigger_new_agent

    def new_agent(self, arguments: AgentArguments) -> Agent:
        agent = self.agent_storage.add_agent(arguments)

        self.trigger_new_agent(agent)

        return agent

