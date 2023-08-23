from __future__ import annotations

import json
from typing import Callable

import redislite

from new_attempt.logic.agent import Agent
from new_attempt.logic.various import Fact, Action
from new_attempt.model.storages.generic_storage import VectorStorage


class AgentStorage:
    def __init__(self,
                 client: redislite.StrictRedis,
                 fact_storage: VectorStorage[Fact],
                 action_storage: VectorStorage[Action],
                 send_new_agent_to_view: Callable[[Agent], None]) -> None:
        self.client = client
        self.fact_storage = fact_storage
        self.action_storage = action_storage
        self.send_new_agent_to_view = send_new_agent_to_view

    def __len__(self) -> int:
        return self.client.dbsize()

    def retrieve_agents(self) -> list[Agent]:
        cursor = "0"
        all_keys = list()

        while cursor != 0:
            cursor, keys = self.client.scan(cursor)
            all_keys.extend(keys)

        agents = [self.get_agent(each_key) for each_key in all_keys]
        return agents

    def get_agent(self, agent_id: str) -> Agent:
        agent_json = self.client.get(agent_id)
        agent_dict = json.loads(agent_json)
        agent = Agent.from_dict(agent_dict, self.fact_storage, self.action_storage)
        return agent

    def next_agent_id(self) -> str:
        current_count = self.client.get("agent_count")
        if current_count is None:
            return "0"
        return str(int(current_count))

    def add_agent(self, agent: Agent) -> None:
        agent_dict = agent.to_dict()
        agent_json = json.dumps(agent_dict)
        self.client.set(agent.agent_id, agent_json)
        self.client.incr("agent_count")
        self.send_new_agent_to_view(agent)

    def remove_agent(self, agent_id: str) -> None:
        self.client.delete(agent_id)
