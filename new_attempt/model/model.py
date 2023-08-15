from typing import Callable

from new_attempt.agent import Agent, AgentArguments
from new_attempt.dummy_data.actions import GLOBAL_ACTIONS
from new_attempt.dummy_data.agents import AGENTS
from new_attempt.dummy_data.facts import GLOBAL_FACTS
from new_attempt.model.storages.action_storage import ActionStorage
from new_attempt.model.storages.agent_storage import AgentStorage
from new_attempt.model.storages.fact_storage import FactStorage


class Model:
    def __init__(self, trigger_new_agent: Callable[[Agent], None]) -> None:
        self.agent_storage = AgentStorage(_agents=AGENTS)
        self.action_storage = ActionStorage(_actions=GLOBAL_ACTIONS)   # same data source as in agent.Agent
        self.fact_storage = FactStorage(_facts=GLOBAL_FACTS)           # same data source as in agent.Agent

        self.trigger_new_agent = trigger_new_agent

    def new_agent(self, arguments: AgentArguments) -> Agent:
        agent = self.agent_storage.add_agent(arguments)

        self.trigger_new_agent(agent)

        return agent

