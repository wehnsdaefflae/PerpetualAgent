from __future__ import annotations
import threading
from dataclasses import asdict
from typing import Literal

from new_attempt.logic.various import AgentArguments, Step, Fact, Action
from new_attempt.model.storages.generic_storage import VectorStorage


class Agent(threading.Thread):
    @staticmethod
    def from_dict(agent_dict: dict[str, any], fact_storage: VectorStorage[Fact], action_storage: VectorStorage[Action]) -> Agent:
        agent_arguments = AgentArguments(**agent_dict["arguments"])

        return Agent(
            agent_dict["agent_id"],
            agent_arguments,
            fact_storage=fact_storage,
            action_storage=action_storage,
            max_steps=agent_dict["max_steps"],
            _status=agent_dict["status"],
            _summary=agent_dict["summary"],
            _past_steps=agent_dict["past_steps"],
        )

    def __init__(self,
                 agent_id: str, arguments: AgentArguments,
                 fact_storage: VectorStorage[Fact], action_storage: VectorStorage[Action], max_steps: int = 20,
                 _status: Literal["finished", "pending", "working", "paused"] = "pending", _summary: str = "", _past_steps: list[Step] | None = None) -> None:
        super().__init__()
        self.agent_id = agent_id
        self.arguments = arguments

        self.status = _status
        self.summary = _summary

        self.max_steps = max_steps
        if _past_steps is None:
            self.past_steps = list[Step]()
        else:
            self.past_steps = list[Step](_past_steps[-max_steps:])

        self.fact_storage = fact_storage
        self.action_storage = action_storage

    def to_dict(self) -> dict[str, any]:
        return {
            "agent_id":     self.agent_id,
            "arguments":    asdict(self.arguments),
            "max_steps":    self.max_steps,
            "status":       self.status,
            "summary":      self.summary,
            "past_steps":   self.past_steps,
        }

    def _infer(self, user_input: str, summary: str) -> str:
        thought = ""

        pass

    def _retrieve_action_from_repo(self, thought: str) -> str:
        action = self.global_action_storage.retrieve_action(thought)
        if action is None:
            action = ""
        return action

    def _retrieve_facts_from_memory(self, thought: str) -> list[str]:
        return self.global_fact_storage.retrieve_facts(thought)

    def _extract_parameters(self, thought: str, retrieved_facts: list[str], selected_action: str) -> dict[str, any]:
        pass

    def _execute_action(self, selected_action: str, action_params: dict[str, any]) -> str:
        pass

    def _generate_fact(self, thought: str, result: str) -> tuple[str, bool]:
        pass

    def _update_initiate_summary(self, request: str, previous_summary: str, new_fact: str) -> tuple[str, bool]:
        pass

    def _increase_action_value(self, action: str) -> None:
        # add, if not present
        self.global_action_storage.add_action(str(len(self.global_action_storage)), action)
        # increase success count
        pass

    def _decrease_action_value(self, action: str) -> None:
        # decrease success count
        c = 0
        # remove if below threshold
        if c < 0:
            self.global_action_storage.remove_action(action)
        pass

    def _save_summary(self, summary: str, is_fulfilled: bool) -> None:
        pass

    def run(self) -> None:
        iteration = 0

        while self.status == "working":
            thought = self._infer(self.arguments.task, self.summary)
            selected_action = self._retrieve_action_from_repo(thought)
            retrieved_facts = self._retrieve_facts_from_memory(thought)
            action_params = self._extract_parameters(thought, retrieved_facts, selected_action)
            result = self._execute_action(selected_action, action_params)

            new_fact, was_successful = self._generate_fact(thought, result)
            self.global_fact_storage.add_fact(new_fact)
            if was_successful:
                self._increase_action_value(selected_action)
            else:
                self._decrease_action_value(selected_action)

            self.summary, is_fulfilled = self._update_initiate_summary(self.arguments.task, self.summary, new_fact)
            self._save_summary(self.summary, is_fulfilled)

            iteration += 1
