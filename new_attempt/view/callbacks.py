from typing import Callable

from new_attempt.model.agent.agent import AgentArguments, Agent
from new_attempt.model.agent.step_elements import Fact, Action


class ViewCallbacks:
    def __init__(self,
                 create_agent: Callable[[AgentArguments], Agent],
                 get_agents: Callable[[list[str] | None], list[Agent]],
                 get_facts: Callable[[list[str] | None, str | None], list[Fact]],
                 get_actions: Callable[[list[str] | None, str | None], list[Action]],
                 pause_agent: Callable[[Agent], None],
                 start_agent: Callable[[Agent], None],
                 delete_agent: Callable[[Agent], None]) -> None:

        self._create_agent = create_agent
        self._get_agents = get_agents
        self._get_facts = get_facts
        self._get_actions = get_actions
        self._pause_agent = pause_agent
        self._start_agent = start_agent
        self._delete_agent = delete_agent

    def create_agent(self, arguments: AgentArguments) -> Agent:
        return self._create_agent(arguments)

    def get_agents(self, agent_ids: list[str] | None = None) -> list[Agent]:
        return self._get_agents(agent_ids)

    def get_facts(self, fact_ids: list[str] | None = None, agent_id: str | None = None) -> list[Fact]:
        return self._get_facts(fact_ids, agent_id)

    def get_actions(self, action_ids: list[str] | None = None, agent_id: str | None = None) -> list[Action]:
        return self._get_actions(action_ids, agent_id)

    def pause_agent(self, agent: Agent) -> None:
        self._pause_agent(agent)

    def start_agent(self, agent: Agent) -> None:
        self._start_agent(agent)

    def delete_agent(self, agent: Agent) -> None:
        self._delete_agent(agent)
