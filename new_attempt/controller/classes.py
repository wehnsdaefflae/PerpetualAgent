from __future__ import annotations

import time
from dataclasses import dataclass

from new_attempt.model.storages.generic_storage import ContentElement


class Fact(ContentElement):
    @staticmethod
    def from_dict(element_dict: dict[str, any]) -> Fact:
        content = element_dict["content"]
        kwargs = element_dict["kwargs"]
        created = kwargs["timestamp"]
        retrieved = kwargs["retrieved"]
        fact = Fact(content, created=created, retrieved=retrieved)
        fact.storage_id = element_dict["storage_id"]
        return fact

    def __init__(self, content: str, created: float = time.time(), retrieved: float | None = None) -> None:
        super().__init__(content, timestamp=created, retrieved=retrieved or created)

    @property
    def created(self) -> float:
        return self._kwargs["created"]

    @created.setter
    def created(self, created: float) -> None:
        self._kwargs["created"] = created

    @property
    def retrieved(self) -> float:
        return self._kwargs["retrieved"]

    @retrieved.setter
    def retrieved(self, retrieved: float) -> None:
        self._kwargs["retrieved"] = retrieved


class Action(ContentElement):
    @staticmethod
    def from_dict(element_dict: dict[str, any]) -> Action:
        content = element_dict["content"]
        kwargs = element_dict["kwargs"]
        success = kwargs["success"]
        failure = kwargs["failure"]
        action = Action(content, success=success, failure=failure)
        action.storage_id = element_dict["storage_id"]
        return action

    def __init__(self, content: str, success: int = 0, failure: int = 0) -> None:
        super().__init__(content, success=success, failure=failure)

    @property
    def success(self) -> int:
        return self._kwargs["success"]

    @success.setter
    def success(self, success: int) -> None:
        self._kwargs["success"] = success

    @property
    def failure(self) -> int:
        return self._kwargs["failure"]

    @failure.setter
    def failure(self, failure: int) -> None:
        self._kwargs["failure"] = failure


@dataclass
class AgentArguments:
    task:                   str

    read_facts_global:      bool
    read_actions_global:    bool
    write_facts_local:      bool
    write_actions_local:    bool

    confirm_actions:        bool
    action_attempts:         int

    llm_thought:            str
    llm_action:             str
    llm_parameter:          str
    llm_result:             str
    llm_fact:               str
    llm_summary:            str


ActionArguments = dict[str, any]
