from __future__ import annotations

import time
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import TypeVar, Type

from new_attempt.model.storages.generic_storage import ContentElement


D = TypeVar("D", bound="Dictable")


class Dictable(ABC):
    @staticmethod
    @abstractmethod
    def from_dict(element_dict: dict[str, any]) -> D:
        raise NotImplementedError()

    @abstractmethod
    def to_dict(self) -> dict[str, any]:
        raise NotImplementedError()


class Thought(str, Dictable):
    @staticmethod
    def from_dict(element_dict: dict[str, any]) -> Thought:
        content = element_dict["content"]
        thought = Thought(content)
        return thought

    def __new__(cls: Type[Thought], value: str, *args: any, **kwargs: any) -> Thought:
        return super().__new__(cls, value)

    def to_dict(self) -> dict[str, any]:
        return {
            "thought": str(self)
        }


class Fact(ContentElement, Dictable):
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


class Action(ContentElement, Dictable):
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


class ActionArguments(dict[str, any], Dictable):
    @staticmethod
    def from_dict(element_dict: dict[str, any]) -> ActionArguments:
        return ActionArguments(element_dict)

    def to_dict(self) -> dict[str, any]:
        return self


class ActionOutput(str, Dictable):
    @staticmethod
    def from_dict(element_dict: dict[str, any]) -> ActionOutput:
        content = element_dict["action_output"]
        return ActionOutput(content)

    def to_dict(self) -> dict[str, any]:
        return {
            "action_output": str(self)
        }


class ActionWasSuccessful(Dictable):
    @staticmethod
    def from_dict(element_dict: dict[str, any]) -> D:
        value = element_dict["action_was_successful"]
        return ActionWasSuccessful(value)

    def to_dict(self) -> dict[str, any]:
        return {
            "action_was_successful": self.value
        }

    def __init__(self, value: bool) -> None:
        self.value = value


class Summary(str, Dictable):
    @staticmethod
    def from_dict(element_dict: dict[str, any]) -> Summary:
        content = element_dict["summary"]
        return Summary(content)

    def to_dict(self) -> dict[str, any]:
        return {
            "summary": str(self)
        }


class IsFulfilled(Dictable):
    @staticmethod
    def from_dict(element_dict: dict[str, any]) -> D:
        value = element_dict["is_fulfilled"]
        return IsFulfilled(value)

    def to_dict(self) -> dict[str, any]:
        return {
            "is_fulfilled": self.value
        }

    def __init__(self, value: bool) -> None:
        self.value = value


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


