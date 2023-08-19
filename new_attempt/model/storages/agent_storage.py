from __future__ import annotations
from new_attempt.agent import Agent


class AgentStorage:
    def __init__(self, _agents: dict[str, Agent] | None = None) -> None:
        if _agents is None:
            self.agents = dict()
        else:
            self.agents = dict(_agents)

    def __len__(self) -> int:
        return len(self.agents)

    def retrieve_agents(self) -> list[Agent]:
        return sorted(self.agents.values(), key=lambda agent: agent.agent_id)

    def get_agent(self, agent_id: str) -> Agent:
        return self.agents[agent_id]

    def add_agent(self, agent: Agent) -> Agent:
        agent_id = f"{len(self.agents)}"
        agent_arguments = agent.arguments
        agent = Agent(agent_id, agent_arguments)
        self.agents[agent_id] = agent
        return agent

    def remove_agent(self, agent_id: str) -> None:
        self.agents.pop(agent_id)
