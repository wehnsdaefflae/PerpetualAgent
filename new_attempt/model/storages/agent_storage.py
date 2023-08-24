from __future__ import annotations

import json

import redislite

from new_attempt.controller.classes import Fact, Action
from new_attempt.logic.agent import Agent
from new_attempt.model.storages.generic_storage import VectorStorage


class AgentStorage:
    def __init__(self,
                 client: redislite.StrictRedis,
                 fact_storage: VectorStorage[Fact],
                 action_storage: VectorStorage[Action]) -> None:
        self.client = client
        self.fact_storage = fact_storage
        self.action_storage = action_storage

    def __len__(self) -> int:
        return self.client.dbsize()

    def retrieve_agents(self) -> list[Agent]:
        cursor = "0"
        all_keys = list()

        while cursor != 0:
            cursor, keys = self.client.scan(cursor)
            all_keys.extend(keys)

        agents = [self.get_agent(each_key) for each_key in all_keys if each_key.startswith("agent:")]
        return agents

    def get_agent(self, agent_id: str) -> Agent:
        agent_json = self.client.get(agent_id)
        agent_dict = json.loads(agent_json)
        agent = Agent.from_dict(agent_dict, self.fact_storage, self.action_storage)
        return agent

    def next_agent_id(self) -> str:
        current_count = self.client.get("metadata:agent_count")
        if current_count is None:
            current_count = 0
        return f"agent:{current_count}"

    def add_agent(self, agent: Agent) -> None:
        agent_dict = agent.to_dict()
        agent_json = json.dumps(agent_dict)
        is_update = self.client.exists(agent.agent_id)
        self.client.set(agent.agent_id, agent_json)

        if not is_update:
            self.client.incr("metadata:agent_count")

    def remove_agent(self, agent_id: str) -> None:
        self.client.delete(agent_id)
