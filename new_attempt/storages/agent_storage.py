from new_attempt.agent import Agent


class AgentStorage:
    def __init__(self) -> None:
        self._agents = dict()

    def retrieve_agent(self, agent_id: str) -> Agent:
        return self._agents[agent_id]

    def add_agent(self, agent: Agent) -> None:
        self._agents[agent.agent_id] = agent

    def remove_agent(self, agent_id: str) -> None:
        self._agents.pop(agent_id)

