from __future__ import annotations

import json

import redislite

from new_attempt.model.agent.agent import Agent, AgentArguments
from new_attempt.model.agent.step_elements import Fact, Action
from new_attempt.model.storages.agent_storage.callbacks import Callbacks
from new_attempt.model.agent.callbacks import Callbacks as AgentCallbacks
from new_attempt.model.storages.vector_storage.storage import VectorStorage


class AgentStorage:
    def __init__(self,
                 client: redislite.StrictRedis,
                 fact_storage: VectorStorage[Fact],
                 action_storage: VectorStorage[Action]) -> None:
        self.client = client
        self.agent_callbacks = None
        self.fact_storage = fact_storage
        self.action_storage = action_storage
        self.callbacks = None

    def __len__(self) -> int:
        return self.client.dbsize()

    def _next_agent_id(self) -> str:
        current_count = self.client.get("metadata:agent_count")
        if current_count is None:
            current_count = 0
        return f"agent:{current_count}"

    def _add_agent(self, agent: Agent) -> None:
        agent_dict = agent.to_dict()
        agent_json = json.dumps(agent_dict)
        is_update = self.client.exists(agent.agent_id)
        self.client.set(agent.agent_id, agent_json)

        if not is_update:
            self.client.incr("metadata:agent_count")

        self.callbacks.upsert_agent(agent)

    def _get_all_agent_ids(self) -> list[str]:
        cursor = "0"
        all_ids = list()

        while cursor != 0:
            cursor, keys = self.client.scan(cursor)
            all_ids.extend(keys)

        return [each_key for each_key in all_ids if each_key.startswith("agent:")]

    def _get_agent(self, agent_id: str) -> Agent:
        agent_json = self.client.get(agent_id)
        agent_dict = json.loads(agent_json)
        agent = Agent.from_dict(agent_dict, self.fact_storage, self.action_storage, self.agent_callbacks)
        return agent

    def connect_callbacks(self, callbacks: Callbacks) -> None:
        self.callbacks = callbacks

    def connect_agent_callbacks(self, agent_callbacks: AgentCallbacks) -> None:
        self.agent_callbacks = agent_callbacks

    def get_agents(self, agent_ids: list[str] | None = None) -> list[Agent]:
        agent_ids = agent_ids or self._get_all_agent_ids()
        return [self._get_agent(agent_id) for agent_id in agent_ids]

    def create_agent(self, arguments: AgentArguments) -> Agent:
        agent_id = self._next_agent_id()
        agent = Agent(agent_id, arguments, self.fact_storage, self.action_storage, self.agent_callbacks)
        self._add_agent(agent)
        return agent

    def remove_agent(self, agent: Agent) -> None:
        self.client.delete(agent.agent_id)
        self.callbacks.remove_agent(agent)
