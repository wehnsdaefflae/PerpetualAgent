import json
from dataclasses import dataclass
from typing import Literal, Callable

import chromadb
import redislite
from chromadb.api.models.Collection import Collection

from new_attempt.agent import AgentArguments
from new_attempt.model.storages.action_interface import ActionInterface
from new_attempt.model.storages.agent_interface import AgentInterface
from new_attempt.model.storages.fact_interface import FactInterface


@dataclass
class StepModel:
    thought: str
    action_id: str
    action_is_local: bool
    arguments: dict[str, any]
    result: str
    fact_id: str
    fact_is_local: bool


@dataclass
class AgentModel:
    agent_id: str
    arguments: AgentArguments
    summary: str
    past_steps: list[StepModel]
    max_steps: int = 20
    status: Literal["running", "paused", "stopped"] = "paused"


class Model:
    def __init__(self, send_new_agent_to_view: Callable[[AgentModel], None]) -> None:
        redis_dbs = {
            "agents":           0,
            "global_facts":     1,
            "global_actions":   2,
            "local_facts":      3,
            "local_actions":    4,
        }
        redis_db_path = "../resources/redis.db"
        redis_config = {"decode_responses": True, "dbserverconfig": {"appendonly": "yes"}}
        self.agent_database = redislite.StrictRedis(redis_db_path, db=0, **redis_config)
        self.agent_interface = AgentInterface(self.agent_database)

        chroma_db_path = "../resources/chroma.db"
        self.chroma_client = chromadb.PersistentClient(path=chroma_db_path)

        global_fact_database = self.chroma_client.get_collection("global_facts")
        global_action_database = self.chroma_client.get_collection("global_actions")

        self.global_fact_interface = FactInterface(global_fact_database)
        self.global_action_interface = ActionInterface(global_action_database)

        self.send_new_agent_to_view = send_new_agent_to_view

    def create_local_facts_collection(self, agent_id: str) -> Collection:
        collection = self.chroma_client.create_collection(f"local_facts_{agent_id}")
        return collection

    def create_local_actions_collection(self, agent_id: str) -> Collection:
        collection = self.chroma_client.create_collection(f"local_actions_{agent_id}")
        return collection

    def get_next_agent_id(self) -> str:
        return f"{self.agent_database.dbsize()}"

    def add_agent(self, agent_model: AgentModel) -> None:
        agent_id = agent_model.agent_id
        agent_json = json.dumps(agent_model)
        self.agent_database.set(agent_id, agent_json)
        self.send_new_agent_to_view(agent_model)

    def get_agent(self, agent_id: str) -> AgentModel:
        agent_json = self.agent_database.get(agent_id)
        agent_dict = json.loads(agent_json)
        return AgentModel(**agent_dict)
