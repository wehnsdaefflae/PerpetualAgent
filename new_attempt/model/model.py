import os

import chromadb
import redislite

from new_attempt.controller.classes import Fact, Action
from new_attempt.model.storages.agent_storage import AgentStorage
from new_attempt.model.storages.generic_storage import VectorStorage


class Model:
    def __init__(self) -> None:
        os.makedirs("../resources/databases", exist_ok=True)

        chroma_db_path = "../resources/databases/chroma.db"
        chroma_client = chromadb.PersistentClient(path=chroma_db_path)

        fact_database = chroma_client.get_or_create_collection("facts")
        action_database = chroma_client.get_or_create_collection("actions")

        self.fact_storage = VectorStorage[Fact](fact_database, Fact)
        self.action_storage = VectorStorage[Action](action_database, Action)

        redis_dbs = {
            "agents":    0,
            "facts":     1,
            "actions":   2,
        }
        redis_db_path = "../resources/databases/redis.db"
        redis_config = {"decode_responses": True, "serverconfig": {"appendonly": "yes"}}
        agent_database = redislite.StrictRedis(redis_db_path, db=0, **redis_config)
        self.agent_storage = AgentStorage(
            agent_database,
            self.fact_storage,
            self.action_storage
        )
