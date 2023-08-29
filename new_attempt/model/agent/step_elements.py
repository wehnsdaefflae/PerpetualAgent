from __future__ import annotations

import time
from typing import Type

from new_attempt.model.storages.vector_storage.element import ContentElement
from new_attempt.utils import Dictable


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
        return self.kwargs["created"]

    @created.setter
    def created(self, created: float) -> None:
        self.kwargs["created"] = created

    @property
    def retrieved(self) -> float:
        return self.kwargs["retrieved"]

    @retrieved.setter
    def retrieved(self, retrieved: float) -> None:
        self.kwargs["retrieved"] = retrieved


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
        return self.kwargs["success"]

    @success.setter
    def success(self, success: int) -> None:
        self.kwargs["success"] = success

    @property
    def failure(self) -> int:
        return self.kwargs["failure"]

    @failure.setter
    def failure(self, failure: int) -> None:
        self.kwargs["failure"] = failure


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
    def from_dict(element_dict: dict[str, any]) -> ActionWasSuccessful:
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
    def from_dict(element_dict: dict[str, any]) -> IsFulfilled:
        value = element_dict["is_fulfilled"]
        return IsFulfilled(value)

    def to_dict(self) -> dict[str, any]:
        return {
            "is_fulfilled": self.value
        }

    def __init__(self, value: bool) -> None:
        self.value = value


class ActionAttempt(Dictable):
    @staticmethod
    def from_dict(arguments_dict: dict[str, any]) -> ActionAttempt:
        return ActionAttempt(**arguments_dict)

    def __init__(self,
                 action: Action | None = None, action_arguments: ActionArguments | None = None,
                 output: ActionOutput | None = None, fact: Fact | None = None,
                 was_successful: ActionWasSuccessful | None = None) -> None:
        self.action = action
        self.action_arguments = action_arguments
        self.output = output
        self.fact = fact
        self.was_successful = was_successful

    def to_dict(self) -> dict[str, any]:
        return {
            "action": self.action.to_dict() if self.action is not None else None,
            "action_arguments": self.action_arguments.to_dict() if self.action_arguments is not None else None,
            "output": self.output.to_dict() if self.output is not None else None,
            "fact": self.fact.to_dict() if self.fact is not None else None,
            "was_successful": self.was_successful.to_dict() if self.was_successful is not None else None,
        }


class Step(Dictable):
    @staticmethod
    def from_dict(history_dict: dict[str, any]) -> Step:
        thought = history_dict["thought"]
        relevant_facts = history_dict["relevant_facts"]
        action_attempts = history_dict["action_attempts"]
        is_fulfilled = history_dict["is_fulfilled"]
        summary = history_dict["summary"]
        return Step(
            thought=Thought.from_dict(thought),
            relevant_facts=[Fact.from_dict(each_fact) for each_fact in relevant_facts],
            action_attempts=[ActionAttempt.from_dict(each_attempt) for each_attempt in action_attempts],
            is_fulfilled=IsFulfilled.from_dict(is_fulfilled),
            summary=Summary.from_dict(summary),
        )

    def __init__(self,
                 thought: Thought | None = None,
                 relevant_facts: list[Fact] | None = None,
                 action_attempts: list[ActionAttempt] | None = None,
                 is_fulfilled: IsFulfilled | None = None,
                 summary: Summary | None = None) -> None:
        self._thought = thought
        self._relevant_facts = relevant_facts
        self._action_attempts = action_attempts or list[ActionAttempt]()
        self._is_fulfilled = is_fulfilled
        self._summary = summary

    @property
    def thought(self) -> Thought | None:
        return self._thought

    @thought.setter
    def thought(self, thought: Thought) -> None:
        self._thought = thought

    @property
    def relevant_facts(self) -> list[Fact] | None:
        return self._relevant_facts

    @relevant_facts.setter
    def relevant_facts(self, relevant_facts: list[Fact]) -> None:
        self._relevant_facts = relevant_facts

    @property
    def action_attempts(self) -> list[ActionAttempt]:
        return self._action_attempts

    @action_attempts.setter
    def action_attempts(self, action_attempts: list[ActionAttempt]) -> None:
        self._action_attempts = action_attempts

    @property
    def is_fulfilled(self) -> IsFulfilled | None:
        return self._is_fulfilled

    @is_fulfilled.setter
    def is_fulfilled(self, is_fulfilled: IsFulfilled) -> None:
        self._is_fulfilled = is_fulfilled

    @property
    def summary(self) -> Summary | None:
        return self._summary

    @summary.setter
    def summary(self, summary: Summary) -> None:
        self._summary = summary

    def to_dict(self) -> dict[str, any]:
        return {
            "thought": self.thought.to_dict() if self.thought is not None else None,
            "relevant_facts": [each_fact.to_dict() for each_fact in self.relevant_facts] if self.relevant_facts is not None else None,
            "action_attempts": [each_attempt.to_dict() for each_attempt in self.action_attempts] if self.action_attempts is not None else None,
            "is_fulfilled": self.is_fulfilled.to_dict(),
            "summary": self.summary.to_dict() if self.summary is not None else None,
        }
