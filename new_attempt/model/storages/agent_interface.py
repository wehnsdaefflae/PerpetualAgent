from __future__ import annotations

import json

import redislite

from new_attempt.agent import Agent


class AgentInterface:
    def __init__(self, client: redislite.StrictRedis) -> None:
        self.client = client

    def __len__(self) -> int:
        return self.client.dbsize()

    def retrieve_agents(self) -> list[Agent]:
        cursor = "0"
        all_keys = list()

        while cursor != 0:
            cursor, keys = self.client.scan(cursor)
            all_keys.extend(keys)

        agents = list()
        for each_key in all_keys:
            agent_json = self.client.get(each_key)
            agent_dict = json.loads(agent_json)
            agent = Agent.from_dict(agent_dict)
            agents.append(agent)

        return agents

    def get_agent(self, agent_id: str) -> Agent:
        agent_json = self.client.get(agent_id)
        agent_dict = json.loads(agent_json)
        agent = Agent.from_dict(agent_dict)

        return agent

    def get_next_id(self) -> str:
        return f"{len(self)}"

    def add_agent(self, agent: Agent) -> None:
        agent_dict = agent.to_dict()
        agent_json = json.dumps(agent_dict)
        self.client.set(agent.agent_id, agent_json)

    def remove_agent(self, agent_id: str) -> None:
        self.client.delete(agent_id)
