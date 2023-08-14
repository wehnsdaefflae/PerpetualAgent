from new_attempt.agent import Agent, AgentArguments


class AgentStorage:
    def __init__(self, _agents: dict[str, Agent] | None = None) -> None:
        if _agents is None:
            self._agents = dict()
        else:
            self._agents = dict(_agents)

    def retrieve_agents(self) -> list[Agent]:
        return sorted(self._agents.values(), key=lambda agent: agent.agent_id)

    def get_agent(self, agent_id: str) -> Agent:
        return self._agents[agent_id]

    def add_agent(self, agent_arguments: AgentArguments) -> Agent:
        agent_id = f"{len(self._agents)}"
        agent = Agent(agent_id, agent_arguments)
        self._agents[agent_id] = agent
        return agent

    def remove_agent(self, agent_id: str) -> None:
        self._agents.pop(agent_id)
